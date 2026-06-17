from django.contrib import admin

from apps.messages.models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "client", "assigned_to", "created_at")
    list_filter = ("shop", "assigned_to")
    search_fields = ("client__instagram_username", "client__display_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "direction", "sent_at", "created_at")
    list_filter = ("direction", "chat__shop")
    search_fields = ("content", "external_id")
