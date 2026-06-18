from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Shop, User, UserRole
from apps.common.permissions import IsAdmin, IsShopMember
from apps.integrations.instagram_oauth import (
    InstagramOAuthError,
    build_authorization_url,
    connect_mock_account,
    connect_with_authorization_code,
    disconnect_instagram,
    get_connection_status,
    is_oauth_configured,
    mock_oauth_enabled,
    parse_oauth_state,
    refresh_connection_token,
)
from apps.integrations.models import InstagramConnection


def _settings_redirect(query: str) -> HttpResponseRedirect:
    return HttpResponseRedirect(f"{settings.FRONTEND_URL}/settings?{query}")


class InstagramStatusView(APIView):
    permission_classes = [IsShopMember]

    def get(self, request):
        shop = request.user.shop
        if not shop:
            return Response(
                {"detail": "User is not linked to a shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        can_manage = request.user.role == UserRole.ADMIN
        return Response(get_connection_status(shop=shop, can_manage=can_manage))


class InstagramConnectView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        shop = request.user.shop
        if not shop:
            return Response(
                {"detail": "User is not linked to a shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if InstagramConnection.objects.filter(shop=shop).exists():
            return Response(
                {"detail": "Instagram is already connected for this shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_oauth_configured():
            return Response(
                {
                    "authorization_url": None,
                    "mock_available": mock_oauth_enabled(),
                    "detail": (
                        "Meta OAuth is not configured. Use mock connect in development."
                        if mock_oauth_enabled()
                        else "Meta OAuth is not configured."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "authorization_url": build_authorization_url(
                    shop_id=shop.id,
                    user_id=request.user.id,
                ),
                "mock_available": False,
            }
        )


class InstagramMockConnectView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        if not mock_oauth_enabled():
            return Response(
                {"detail": "Mock Instagram connect is not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shop = request.user.shop
        if not shop:
            return Response(
                {"detail": "User is not linked to a shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if InstagramConnection.objects.filter(shop=shop).exists():
            return Response(
                {"detail": "Instagram is already connected for this shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        connection = connect_mock_account(shop=shop, connected_by=request.user)
        payload = get_connection_status(shop=shop, can_manage=True)
        payload["message"] = f"Connected @{connection.instagram_username} (mock)."
        return Response(payload, status=status.HTTP_201_CREATED)


class InstagramCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error = request.GET.get("error")
        if error:
            description = request.GET.get("error_description", error)
            return _settings_redirect(
                f"instagram=error&message={description.replace(' ', '+')}"
            )

        code = request.GET.get("code")
        state = request.GET.get("state")
        if not code or not state:
            return _settings_redirect("instagram=error&message=Missing+OAuth+parameters")

        try:
            payload = parse_oauth_state(state)
            shop = get_object_or_404(Shop, id=payload["shop_id"])
            connected_by = get_object_or_404(User, id=payload["user_id"])
            connect_with_authorization_code(
                shop=shop,
                connected_by=connected_by,
                code=code,
            )
        except InstagramOAuthError as exc:
            return _settings_redirect(
                f"instagram=error&message={exc.message.replace(' ', '+')}"
            )
        except Exception:
            return _settings_redirect("instagram=error&message=OAuth+callback+failed")

        return _settings_redirect("instagram=connected")


class InstagramDisconnectView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        shop = request.user.shop
        if not shop:
            return Response(
                {"detail": "User is not linked to a shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        disconnect_instagram(shop=shop)
        return Response({"message": "Instagram disconnected."})


class InstagramRefreshView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        shop = request.user.shop
        if not shop:
            return Response(
                {"detail": "User is not linked to a shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            connection = shop.instagram_connection
        except InstagramConnection.DoesNotExist:
            return Response(
                {"detail": "Instagram is not connected for this shop."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh_connection_token(connection)
        except InstagramOAuthError as exc:
            return Response({"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(get_connection_status(shop=shop, can_manage=True))
