from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client
from apps.clients.search import search_clients
from apps.clients.serializers import (
    ClientCardSerializer,
    ClientNotesUpdateSerializer,
    ClientSearchResultSerializer,
    ClientSerializer,
)
from apps.common.permissions import ClientPermission, IsAdminOrManager, IsShopMember
from apps.common.viewsets import ShopQuerysetMixin


class ClientViewSet(ShopQuerysetMixin, viewsets.ModelViewSet):
    queryset = Client.objects.select_related("shop").all().order_by("instagram_username")
    serializer_class = ClientSerializer
    permission_classes = [ClientPermission]

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)


class ClientCardView(APIView):
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsShopMember()]
        return [IsAdminOrManager(), IsShopMember()]

    def get_client(self, request, client_id: int) -> Client:
        return get_object_or_404(
            Client.objects.prefetch_related("orders").filter(shop=request.user.shop),
            id=client_id,
        )

    def get(self, request, client_id: int):
        client = self.get_client(request, client_id)
        serializer = ClientCardSerializer(client, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, client_id: int):
        client = self.get_client(request, client_id)
        serializer = ClientNotesUpdateSerializer(
            client,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        card = ClientCardSerializer(client, context={"request": request})
        return Response(card.data)


class ClientSearchView(APIView):
    permission_classes = [IsShopMember]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response([])

        results = search_clients(
            shop=request.user.shop,
            user=request.user,
            query=query,
        )
        serializer = ClientSearchResultSerializer(results, many=True)
        return Response(serializer.data)
