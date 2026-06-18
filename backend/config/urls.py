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
    path("api/", include(router.urls)),
]
