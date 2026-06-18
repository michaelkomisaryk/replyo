from django.contrib import admin

from apps.integrations.models import InstagramConnection, InstagramWebhookEvent


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


@admin.register(InstagramWebhookEvent)
class InstagramWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "shop", "processed_at", "created_at", "error")
    search_fields = ("event_id", "shop__name")
    readonly_fields = ("created_at", "updated_at")
