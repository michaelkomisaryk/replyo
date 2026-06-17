from django.contrib import admin

from apps.accounts.models import Shop, User
from apps.accounts.tokens import EmailVerificationToken


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "shop",
        "role",
        "is_email_verified",
        "is_active",
    )
    list_filter = ("role", "is_active", "is_email_verified", "shop")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token", "expires_at", "created_at")
    search_fields = ("user__email", "token")
