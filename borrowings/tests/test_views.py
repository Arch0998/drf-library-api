from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch

from books.models import Book
from borrowings.models import Borrowing


User = get_user_model()


class BorrowingViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="12345"
        )
        self.client.force_authenticate(user=self.user)
        self.book = Book.objects.create(
            title="Book",
            author="Author",
            cover="HARD",
            inventory=2,
            daily_fee=1.0,
        )
        self.book2 = Book.objects.create(
            title="Book 2",
            author="Author 2",
            cover="SOFT",
            inventory=1,
            daily_fee=1.5,
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user, book=self.book, expected_return_date="2030-01-01"
        )

    def test_list_borrowings(self):
        url = reverse("borrowings:borrowing-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if "results" in response.data:
            self.assertEqual(len(response.data["results"]), 1)
        else:
            self.assertEqual(len(response.data), 1)

    def test_retrieve_borrowing(self):
        url = reverse("borrowings:borrowing-detail", args=[self.borrowing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.borrowing.id)

    @patch("borrowings.serializers.notify_new_borrowing.delay")
    def test_create_borrowing(self, mock_notify_task):
        url = reverse("borrowings:borrowing-list")
        data = {"expected_return_date": "2030-01-10", "book": self.book2.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 2)
        mock_notify_task.assert_called_once()
