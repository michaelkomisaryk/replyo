from rest_framework import viewsets

from apps.accounts.models import Shop, User
from apps.accounts.serializers import ShopSerializer, UserSerializer


class ShopViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Shop.objects.all().order_by("name")
    serializer_class = ShopSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.select_related("shop").all().order_by("username")
    serializer_class = UserSerializer
