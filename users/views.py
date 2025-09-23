from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, mixins, permissions

from users.serializers import (
    UserSerializer,
    RegisterSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


@extend_schema_view(
    create=extend_schema(
        summary="Register User",
        description="Register a new user account. Available to everyone.",
        tags=["Users"],
    )
)
class CreateUserViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    retrieve=extend_schema(
        summary="Current User Profile",
        description="Get detailed information "
        "about the authenticated user (your own profile).",
        tags=["Users"],
    ),
    update=extend_schema(
        summary="Update Current User",
        description="Completely update your own profile information.",
        tags=["Users"],
    ),
    partial_update=extend_schema(
        summary="Partially Update Current User",
        description="Partially update your own profile information.",
        tags=["Users"],
    ),
)
class ManageUserViewSet(
    viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.RetrieveModelMixin
):
    queryset = User.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer
