from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User
from books.models import Book
from borrowings.models import Borrowing


class BorrowingViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="12345"
        )
        self.client.force_authenticate(user=self.user)

        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            cover="HARD",
            inventory=5,
            daily_fee=2.5,
        )

        Borrowing.objects.all().delete()

    def test_create_borrowing_decreases_inventory(self):
        url = reverse("borrowing-list")
        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 4)

    def test_create_borrowing_out_of_stock(self):
        self.book.inventory = 0
        self.book.save()
        url = reverse("borrowing-list")
        data = {
            "book": self.book.id,
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book", response.data)
        self.assertEqual(
            response.data["book"][0], "This book is out of stock."
        )

    def test_return_book_increases_inventory(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.book.inventory -= 1
        self.book.save()

        url = reverse("borrowing-return-book", args=[borrowing.id])
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.book.refresh_from_db()
        self.assertIsNotNone(borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, 5)

    def test_return_book_already_returned(self):
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=date.today(),
        )
        url = reverse("borrowing-return-book", args=[borrowing.id])
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Book already returned.")

    def test_queryset_filter_user_and_is_active(self):
        active_borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
            actual_return_date=date.today(),
        )

        url = reverse("borrowing-list")
        response = self.client.get(
            url, {"user_id": self.user.id, "is_active": "true"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], active_borrowing.id)
