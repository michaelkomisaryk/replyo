from django.contrib import admin

from apps.clients.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "instagram_username", "display_name", "created_at")
    list_filter = ("shop",)
    search_fields = ("instagram_username", "display_name")
