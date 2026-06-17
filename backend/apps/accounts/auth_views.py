from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.auth_serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)
from apps.accounts.tokens import EmailVerificationToken

User = get_user_model()


def _build_auth_response(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserProfileSerializer(user).data,
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        payload = {
            "message": "Registration successful. Please verify your email.",
            "user": UserProfileSerializer(user).data,
        }
        if settings.DEBUG:
            token = user.email_verification_tokens.order_by("-created_at").first()
            if token:
                payload["debug_verification_url"] = (
                    f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
                )
        return Response(payload, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email__iexact=email)
            authenticated = authenticate(
                request,
                username=user.username,
                password=password,
            )
        except User.DoesNotExist:
            authenticated = None

        if not authenticated:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(_build_auth_response(authenticated))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"message": "Logged out successfully."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_value = serializer.validated_data["token"]

        try:
            token = EmailVerificationToken.objects.select_related("user").get(
                token=token_value
            )
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"detail": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token.is_expired:
            return Response(
                {"detail": "Verification token has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token.user
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        EmailVerificationToken.objects.filter(user=user).delete()

        return Response(
            {
                "message": "Email verified successfully.",
                "user": UserProfileSerializer(user).data,
            }
        )
