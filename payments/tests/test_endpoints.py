from decimal import Decimal
from datetime import date, timedelta

from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from payments.models import Payment, PaymentStatus, PaymentType
from books.models import Book
from borrowings.models import Borrowing


class PaymentEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("payments-list")
        self.user = get_user_model().objects.create_user(
            email="user2@example.com", password="testpass123"
        )
        self._book_idx = 0

    def _create_book(self) -> Book:
        self._book_idx += 1
        return Book.objects.create(
            title=f"Book E{self._book_idx}",
            author="Author",
            cover="HARD",
            inventory=10,
            daily_fee=Decimal("1.25"),
        )

    def _create_borrowing(self, *, user=None) -> Borrowing:
        user = user or self.user
        book = self._create_book()
        return Borrowing.objects.create(
            user=user,
            book=book,
            expected_return_date=date.today() + timedelta(days=5),
        )

    def test_list_orders_by_id_desc(self):
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

        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = (
            resp.data["results"]
            if isinstance(resp.data, dict) and "results" in resp.data
            else resp.data
        )
        ids = [item["id"] for item in items]
        self.assertGreaterEqual(len(ids), 2)
        self.assertGreater(ids[0], ids[1])

    def test_create_ignores_read_only_fields(self):
        borrowing = self._create_borrowing()
        payload = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": borrowing.id,
            "money_to_pay": "12.34",
            "session_url": "https://malicious.example/override",
            "session_id": "fake-session",
        }
        resp = self.client.post(self.list_url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(resp.data.get("session_url"))
        self.assertIsNone(resp.data.get("session_id"))

        obj = Payment.objects.get(pk=resp.data["id"])
        self.assertIsNone(obj.session_url)
        self.assertIsNone(obj.session_id)

    def test_create_invalid_payment_type_returns_400(self):
        borrowing = self._create_borrowing()
        payload = {
            "payment_type": "INVALID",
            "borrowing_id": borrowing.id,
            "money_to_pay": "10.00",
        }
        resp = self.client.post(self.list_url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_type", resp.data)

    def test_create_negative_amount_returns_400(self):
        borrowing = self._create_borrowing()
        payload = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": borrowing.id,
            "money_to_pay": "-0.01",
        }
        resp = self.client.post(self.list_url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("money_to_pay", resp.data)

    def test_retrieve_existing(self):
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
