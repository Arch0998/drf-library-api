from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins


from users.serializers import UserSerializer, RegisterSerializer

User = get_user_model()


class CreateUserViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    serializer_class = RegisterSerializer


class ManageUserViewSet(
    viewsets.GenericViewSet,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin
):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
