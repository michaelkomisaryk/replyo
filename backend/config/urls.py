from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import ShopViewSet, UserViewSet
from apps.clients.views import ClientViewSet
from apps.common.views import health_check
from apps.messages.views import ChatViewSet, MessageViewSet
from apps.orders.views import OrderViewSet

router = DefaultRouter()
router.register("shops", ShopViewSet, basename="shop")
router.register("users", UserViewSet, basename="user")
router.register("clients", ClientViewSet, basename="client")
router.register("chats", ChatViewSet, basename="chat")
router.register("messages", MessageViewSet, basename="message")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/", include(router.urls)),
]
