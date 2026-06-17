from django.contrib import admin

from apps.accounts.models import Shop, User


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "shop", "role", "is_active")
    list_filter = ("role", "is_active", "shop")
    search_fields = ("username", "email", "first_name", "last_name")
