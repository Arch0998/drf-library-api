from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="hardcover",
            inventory=5,
            daily_fee=9.99,
        )

        self.list_url = reverse("book-list")
        self.detail_url = reverse(
            "book-detail",
            kwargs={"pk": self.book.pk},
        )

    def test_books_list_unauthorized(self):
        response = self.client.get(self.list_url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_get_valid_book_detail(self):
        response = self.client.get(self.detail_url)

        serializer = BookSerializer(self.book)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_book_detail(self):
        url = reverse("book-detail", kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
