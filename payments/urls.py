from django.urls import path, include
from rest_framework.routers import SimpleRouter
from payments.api import PaymentViewSet


router = SimpleRouter()
router.register(r"payments", PaymentViewSet, basename="payments")
urlpatterns = [
    path("", include(router.urls))
]
