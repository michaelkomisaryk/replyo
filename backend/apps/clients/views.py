from rest_framework import viewsets

from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer
from apps.common.permissions import ClientPermission
from apps.common.viewsets import ShopQuerysetMixin


class ClientViewSet(ShopQuerysetMixin, viewsets.ModelViewSet):
    queryset = Client.objects.select_related("shop").all().order_by("instagram_username")
    serializer_class = ClientSerializer
    permission_classes = [ClientPermission]

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)
