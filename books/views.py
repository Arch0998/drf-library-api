from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from books.models import Book
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    search_fields = ["title", "author"]
    filterset_fields = ["cover", "inventory"]
    ordering_fields = ["title", "author", "inventory", "daily_fee"]
    ordering = ["title", "author"]
