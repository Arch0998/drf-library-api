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

    def test_list_payments(self):
        b1 = self._create_borrowing()
        b2 = self._create_borrowing()

        Payment.objects.create(
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.PAYMENT,
            borrowing=b1,
            money_to_pay=Decimal("10.00"),
        )
        Payment.objects.create(
            status=PaymentStatus.PAID,
            payment_type=PaymentType.FINE,
            borrowing=b2,
            money_to_pay=Decimal("5.00"),
        )

        url = reverse("payments-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = (
            resp.data["results"]
            if isinstance(resp.data, dict) and "results" in resp.data
            else resp.data
        )
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        first = data[0]
        self.assertIn("id", first)
        self.assertIn("status", first)
        self.assertIn("payment_type", first)
        self.assertIn("money_to_pay", first)

    def test_create_payment_success(self):
        borrowing = self._create_borrowing()
        url = reverse("payments-list")
        payload = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": borrowing.id,
            "money_to_pay": "12.34",
        }
        resp = self.client.post(url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["payment_type"], PaymentType.PAYMENT)
        self.assertEqual(resp.data["borrowing_id"], borrowing.id)
        self.assertEqual(resp.data["money_to_pay"], "12.34")
        self.assertEqual(resp.data["status"], PaymentStatus.PENDING)

    def test_create_payment_invalid_status(self):
        borrowing = self._create_borrowing()
        url = reverse("payments-list")
        payload = {
            "status": "INVALID",
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": borrowing.id,
            "money_to_pay": "12.34",
        }
        resp = self.client.post(url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", resp.data)

    def test_retrieve_payment(self):
        borrowing = self._create_borrowing()
        p = Payment.objects.create(
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.FINE,
            borrowing=borrowing,
            money_to_pay=Decimal("0.00"),
        )
        url = reverse("payments-detail", args=[p.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], p.id)
        self.assertEqual(resp.data["payment_type"], PaymentType.FINE)
        self.assertEqual(resp.data["borrowing_id"], borrowing.id)
        self.assertEqual(resp.data["money_to_pay"], "0.00")
