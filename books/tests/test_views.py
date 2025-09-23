from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer


def setup_books(self):
    self.book = Book.objects.create(
        title="Test Book",
        author="Test Author",
        cover="HARD",
        inventory=5,
        daily_fee=9.99,
    )

    self.list_url = reverse("book-list")
    self.detail_url = reverse(
        "book-detail",
        kwargs={"pk": self.book.pk},
    )


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        setup_books(self)

    def test_books_list_unauthorized(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = BookSerializer(self.book)
        self.assertIn(serializer.data, response.data["results"])

    def test_get_valid_book_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = BookSerializer(self.book)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid_book_detail(self):
        url = reverse("book-detail", kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)
        setup_books(self)

    def test_can_list_books(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = BookSerializer(self.book)
        self.assertIn(serializer.data, response.data["results"])

    def test_cannot_create_book(self):
        data = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": 5.99,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_put_update_book(self):
        data = {
            "title": "Updated Book Title",
            "author": "Updated Author",
            "cover": "SOFT",
            "inventory": 15,
            "daily_fee": 12.99,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_patch_update_book(self):
        data = {"inventory": 25}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StaffBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = get_user_model().objects.create_user(
            email="staff@example.com",
            password="staffpass123",
            is_staff=True,
        )
        self.client.force_authenticate(self.staff_user)
        setup_books(self)

    def test_staff_can_create_book(self):
        data = {
            "title": "Staff Book",
            "author": "Staff Author",
            "cover": "HARD",
            "inventory": 20,
            "daily_fee": 7.99,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

        created_book = Book.objects.get(title="Staff Book")
        serializer = BookSerializer(created_book)
        self.assertEqual(response.data, serializer.data)

    def test_staff_can_put_update_book(self):
        data = {
            "title": "Updated Book Title",
            "author": "Updated Author",
            "cover": "SOFT",
            "inventory": 15,
            "daily_fee": 12.99,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.book.refresh_from_db()
        serializer = BookSerializer(self.book)
        self.assertEqual(response.data, serializer.data)

    def test_staff_can_patch_update_inventory(self):
        data = {"inventory": 30}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.book.refresh_from_db()
        serializer = BookSerializer(self.book)
        self.assertEqual(response.data, serializer.data)

    def test_staff_cannot_update_with_invalid_inventory(self):
        data = {"inventory": -5}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inventory", response.data)

    def test_staff_cannot_update_with_invalid_daily_fee(self):
        data = {"daily_fee": -10.00}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("daily_fee", response.data)

    def test_staff_cannot_update_with_invalid_cover(self):
        data = {"cover": "INVALID"}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cover", response.data)

    def test_staff_cannot_update_with_duplicate_title_author_cover(self):
        Book.objects.create(
            title="Another Book",
            author="Another Author",
            cover="HARD",
            inventory=3,
            daily_fee=8.99,
        )

        data = {
            "title": "Another Book",
            "author": "Another Author",
            "cover": "HARD",
            "inventory": 10,
            "daily_fee": 9.99,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
