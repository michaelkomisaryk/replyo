from django.contrib import admin

from apps.orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "client", "chat", "status", "created_at")
    list_filter = ("shop", "status")
    search_fields = ("client__instagram_username", "client__display_name")
