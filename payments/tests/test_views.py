from datetime import timedelta, date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from payments.models import Payment, PaymentStatus, PaymentType
from borrowings.models import Borrowing
from books.models import Book


class PaymentViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self._book_idx = 0

    def _create_book(self) -> Book:
        self._book_idx += 1
        return Book.objects.create(
            title=f"Book {self._book_idx}",
            author="Author",
            cover="HARD",
            inventory=10,
            daily_fee=Decimal("1.50"),
        )

    def _create_borrowing(self, *, user=None) -> Borrowing:
        user = user or self.user
        book = self._create_book()
        return Borrowing.objects.create(
            user=user,
            book=book,
            expected_return_date=date.today() + timedelta(days=7),
        )

    def test_create_payment_success(self):
        self.client.force_authenticate(user=self.user)
        borrowing = self._create_borrowing()
        url = reverse("payments:payment-list")
        payload = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing": borrowing.id,
            "money_to_pay": "12.34",
        }
        resp = self.client.post(url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["payment_type"], PaymentType.PAYMENT)
        self.assertEqual(resp.data["borrowing"], borrowing.id)
        self.assertEqual(resp.data["money_to_pay"], "12.34")
        self.assertEqual(resp.data["status"], PaymentStatus.PENDING)

    def test_create_payment_invalid_status(self):
        self.client.force_authenticate(user=self.user)
        borrowing = self._create_borrowing()
        url = reverse("payments:payment-list")
        payload = {
            "status": "INVALID",
            "payment_type": PaymentType.PAYMENT,
            "borrowing": borrowing.id,
            "money_to_pay": "12.34",
        }
        resp = self.client.post(url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", resp.data)
