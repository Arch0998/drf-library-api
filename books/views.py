from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema_view, extend_schema

from core.permissions import IsStaffUser
from books.models import Book
from books.serializers import BookSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List Books",
        description="Get a list of all books. Available to all users.",
        tags=["Books"],
    ),
    create=extend_schema(
        summary="Create Book",
        description="Create a new book. Available only to staff users",
        tags=["Books"],
    ),
    retrieve=extend_schema(
        summary="Book Details",
        description="Get detailed information about a specific book. "
        "Available to all users.",
        tags=["Books"],
    ),
    update=extend_schema(
        summary="Update Book",
        description="Completely update book information. "
        "Available only to staff users",
        tags=["Books"],
    ),
    partial_update=extend_schema(
        summary="Partially Update Book",
        description="Partially update book information. "
        "Available only to staff users",
        tags=["Books"],
    ),
    destroy=extend_schema(
        summary="Delete Book",
        description="Delete a book from the library. "
        "Available only to staff users.",
        tags=["Books"],
    ),
)
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
