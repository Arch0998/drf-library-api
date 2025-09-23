from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from core.permissions import IsStaffUser
from books.models import Book
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    search_fields = ["title", "author"]
    filterset_fields = ["cover", "inventory"]
    ordering_fields = ["title", "author", "inventory", "daily_fee"]
    ordering = ["title", "author"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsStaffUser]
        return [permission() for permission in permission_classes]
