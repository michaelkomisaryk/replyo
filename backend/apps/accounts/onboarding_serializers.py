from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.invitations import TeamInvitation
from apps.accounts.models import UserRole

User = get_user_model()


class InviteTeamMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[UserRole.MANAGER, UserRole.SUPPORT_MANAGER],
    )

    def validate_email(self, value: str) -> str:
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        shop = self.context["shop"]
        email = attrs["email"]
        if TeamInvitation.objects.filter(
            shop=shop,
            email__iexact=email,
            accepted_at__isnull=True,
        ).exists():
            raise serializers.ValidationError(
                {"email": "An invitation for this email is already pending."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        shop = self.context["shop"]
        invited_by = self.context["invited_by"]
        invitation = TeamInvitation.objects.create(
            shop=shop,
            email=validated_data["email"],
            role=validated_data["role"],
            invited_by=invited_by,
        )
        self._send_invitation_email(invitation)
        return invitation

    def _send_invitation_email(self, invitation: TeamInvitation) -> None:
        accept_url = f"{settings.FRONTEND_URL}/accept-invite?token={invitation.token}"
        send_mail(
            subject=f"Join {invitation.shop.name} on Replyo",
            message=(
                f"You have been invited to join {invitation.shop.name} as "
                f"{invitation.get_role_display()}.\n\n"
                f"Accept your invitation: {accept_url}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )


class TeamInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamInvitation
        fields = [
            "id",
            "email",
            "role",
            "accepted_at",
            "expires_at",
            "created_at",
        ]


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    password = serializers.CharField(min_length=8, write_only=True)

    @transaction.atomic
    def create(self, validated_data):
        token_value = validated_data["token"]
        password = validated_data["password"]

        try:
            invitation = TeamInvitation.objects.select_related("shop").get(
                token=token_value
            )
        except TeamInvitation.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid invitation token."})

        if invitation.accepted_at:
            raise serializers.ValidationError(
                {"token": "This invitation has already been accepted."}
            )
        if invitation.is_expired:
            raise serializers.ValidationError({"token": "This invitation has expired."})
        if User.objects.filter(email__iexact=invitation.email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )

        user = User.objects.create_user(
            username=invitation.email,
            email=invitation.email,
            password=password,
            shop=invitation.shop,
            role=invitation.role,
            is_email_verified=True,
        )
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at"])
        return user
