from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.auth_serializers import UserProfileSerializer
from apps.accounts.auth_views import _build_auth_response
from apps.accounts.onboarding import build_onboarding_checklist
from apps.accounts.onboarding_serializers import (
    AcceptInvitationSerializer,
    InviteTeamMemberSerializer,
    TeamInvitationSerializer,
)
from apps.accounts.invitations import TeamInvitation
from apps.common.permissions import IsAdmin, IsShopMember


class OnboardingView(APIView):
    permission_classes = [IsShopMember]

    def get(self, request):
        checklist = build_onboarding_checklist(request.user.shop)
        return Response(checklist)


class InvitationListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        invitations = TeamInvitation.objects.filter(shop=request.user.shop).order_by(
            "-created_at"
        )
        serializer = TeamInvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InviteTeamMemberSerializer(
            data=request.data,
            context={"shop": request.user.shop, "invited_by": request.user},
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        payload = TeamInvitationSerializer(invitation).data
        if settings.DEBUG:
            payload["debug_accept_url"] = (
                f"{settings.FRONTEND_URL}/accept-invite?token={invitation.token}"
            )
        return Response(payload, status=status.HTTP_201_CREATED)


class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Invitation accepted successfully.",
                "user": UserProfileSerializer(user).data,
                **_build_auth_response(user),
            },
            status=status.HTTP_201_CREATED,
        )
