from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from users.views import CreateUserViewSet, ManageUserViewSet


app_name = "users"

router = DefaultRouter()
router.register("register", CreateUserViewSet, basename="register")


urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path(
        "me/", ManageUserViewSet.as_view({"get": "retrieve", "put": "update"})
    ),
]

urlpatterns += router.urls
