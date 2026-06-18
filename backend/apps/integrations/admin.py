from django.contrib import admin

from apps.integrations.models import InstagramConnection


@admin.register(InstagramConnection)
class InstagramConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "instagram_username",
        "shop",
        "instagram_user_id",
        "token_expires_at",
        "created_at",
    )
    search_fields = ("instagram_username", "shop__name")
    readonly_fields = (
        "encrypted_access_token",
        "created_at",
        "updated_at",
    )
