from rest_framework import serializers

from apps.accounts.models import Shop, User


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "name", "settings", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "shop",
            "role",
            "is_active",
            "date_joined",
        ]
