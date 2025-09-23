from django.urls import path, include
from rest_framework.routers import SimpleRouter

from payments.views import PaymentViewSet
from payments import views


router = SimpleRouter()
router.register(r"payments", PaymentViewSet, basename="payments")
urlpatterns = [path("", include(router.urls)),
    path('success/', views.PaymentSuccessView.as_view(), name='success'),
    path('cancel/', views.PaymentCancelView.as_view(), name='cancel'),
]
