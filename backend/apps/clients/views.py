from rest_framework import viewsets

from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer


class ClientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Client.objects.select_related("shop").all().order_by("instagram_username")
    serializer_class = ClientSerializer
