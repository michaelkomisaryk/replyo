from django.contrib import admin

from apps.orders.models import Order, OrderStatusChange


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "client", "chat", "status", "created_at")
    list_filter = ("shop", "status")
    search_fields = ("client__instagram_username", "client__display_name")


@admin.register(OrderStatusChange)
class OrderStatusChangeAdmin(admin.ModelAdmin):
    list_display = ("order", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status",)
