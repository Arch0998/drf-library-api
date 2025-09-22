from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins, permissions

from users.serializers import UserSerializer, RegisterSerializer


User = get_user_model()


class CreateUserViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ManageUserViewSet(
    viewsets.GenericViewSet, mixins.UpdateModelMixin, mixins.RetrieveModelMixin
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
