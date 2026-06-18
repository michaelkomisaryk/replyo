from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.auth_views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    VerifyEmailView,
)
from apps.accounts.onboarding_views import (
    AcceptInvitationView,
    InvitationListCreateView,
    OnboardingView,
)
from apps.integrations.views import (
    InstagramCallbackView,
    InstagramConnectView,
    InstagramDisconnectView,
    InstagramMockConnectView,
    InstagramRefreshView,
    InstagramStatusView,
)
from apps.integrations.webhook_views import InstagramWebhookView
from apps.accounts.views import ShopViewSet, UserViewSet
from apps.clients.views import ClientCardView, ClientViewSet
from apps.common.views import health_check
from apps.messages.views import (
    ChatPrioritiesView,
    ChatReplyView,
    ChatViewSet,
    MessageViewSet,
)
from apps.orders.views import ChatCreateOrderView, OrderStatusHistoryView, OrderViewSet

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
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/auth/verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("api/onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("api/invitations/", InvitationListCreateView.as_view(), name="invitations"),
    path(
        "api/invitations/accept/",
        AcceptInvitationView.as_view(),
        name="invitations-accept",
    ),
    path(
        "api/integrations/instagram/status/",
        InstagramStatusView.as_view(),
        name="instagram-status",
    ),
    path(
        "api/integrations/instagram/connect/",
        InstagramConnectView.as_view(),
        name="instagram-connect",
    ),
    path(
        "api/integrations/instagram/mock-connect/",
        InstagramMockConnectView.as_view(),
        name="instagram-mock-connect",
    ),
    path(
        "api/integrations/instagram/callback/",
        InstagramCallbackView.as_view(),
        name="instagram-callback",
    ),
    path(
        "api/integrations/instagram/disconnect/",
        InstagramDisconnectView.as_view(),
        name="instagram-disconnect",
    ),
    path(
        "api/integrations/instagram/refresh/",
        InstagramRefreshView.as_view(),
        name="instagram-refresh",
    ),
    path(
        "api/integrations/instagram/webhook/",
        InstagramWebhookView.as_view(),
        name="instagram-webhook",
    ),
    path(
        "api/chats/<int:chat_id>/reply/",
        ChatReplyView.as_view(),
        name="chat-reply",
    ),
    path(
        "api/chats/priorities/",
        ChatPrioritiesView.as_view(),
        name="chat-priorities",
    ),
    path(
        "api/clients/<int:client_id>/card/",
        ClientCardView.as_view(),
        name="client-card",
    ),
    path(
        "api/chats/<int:chat_id>/orders/",
        ChatCreateOrderView.as_view(),
        name="chat-create-order",
    ),
    path(
        "api/orders/<int:order_id>/history/",
        OrderStatusHistoryView.as_view(),
        name="order-status-history",
    ),
    path("api/", include(router.urls)),
]
