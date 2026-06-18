from apps.accounts.invitations import TeamInvitation
from apps.accounts.models import UserRole


def build_onboarding_checklist(shop) -> dict:
    admin = shop.members.filter(role=UserRole.ADMIN).order_by("id").first()
    onboarding_settings = shop.settings.get("onboarding", {})

    email_verified = bool(admin and admin.is_email_verified)
    instagram_connected = bool(onboarding_settings.get("instagram_connected", False))
    team_invited = (
        TeamInvitation.objects.filter(shop=shop).exists()
        or shop.members.count() > 1
    )

    steps = [
        {
            "id": "email_verified",
            "label": "Verify your email",
            "completed": email_verified,
            "placeholder": False,
        },
        {
            "id": "instagram_connected",
            "label": "Connect Instagram account",
            "completed": instagram_connected,
            "placeholder": True,
        },
        {
            "id": "team_invited",
            "label": "Invite a team member",
            "completed": team_invited,
            "placeholder": False,
        },
    ]

    return {
        "steps": steps,
        "completed_count": sum(1 for step in steps if step["completed"]),
        "total_count": len(steps),
        "is_complete": all(
            step["completed"] for step in steps if not step["placeholder"]
        ),
    }
