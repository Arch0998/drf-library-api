from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payments.views import (
    PaymentViewSet,
    StripeWebhookView,
    PaymentTestSuccessView,
)
from payments import views


app_name = "payments"

router = DefaultRouter()
router.register("", PaymentViewSet, basename="payments")
urlpatterns = [
    path("success/", views.PaymentSuccessView.as_view(), name="success"),
    path("cancel/", views.PaymentCancelView.as_view(), name="cancel"),
    path("webhook/", StripeWebhookView.as_view(), name="webhook"),
    path(
        "test-success/", PaymentTestSuccessView.as_view(), name="test-success"
    ),
    path("", include(router.urls)),
]
