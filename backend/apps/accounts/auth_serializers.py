from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import Shop, UserRole
from apps.accounts.tokens import EmailVerificationToken

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    shop_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    @transaction.atomic
    def create(self, validated_data):
        shop = Shop.objects.create(name=validated_data["shop_name"])
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            shop=shop,
            role=UserRole.ADMIN,
            is_email_verified=False,
        )
        token = EmailVerificationToken.objects.create(user=user)
        self._send_verification_email(user, token)
        return user

    def _send_verification_email(self, user: User, token: EmailVerificationToken) -> None:
        frontend_url = getattr(settings, "FRONTEND_URL", "http://127.0.0.1:3000")
        verify_url = f"{frontend_url}/verify-email?token={token.token}"
        send_mail(
            subject="Verify your Replyo email",
            message=f"Click to verify your email: {verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )


class UserProfileSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "shop",
            "shop_name",
            "role",
            "is_email_verified",
            "first_name",
            "last_name",
        ]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()
