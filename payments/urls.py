from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payments.views import PaymentViewSet
from payments import views


app_name = "payments"

router = DefaultRouter()
router.register("", PaymentViewSet)
urlpatterns = [
    path("success/", views.PaymentSuccessView.as_view(), name="success"),
    path("cancel/", views.PaymentCancelView.as_view(), name="cancel"),
    path("", include(router.urls)),
]
