from decimal import Decimal

from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from payments.models import Payment, PaymentStatus, PaymentType


class PaymentEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse("payments-list")

    def test_list_orders_by_id_desc(self):
        p1 = Payment.objects.create(
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.PAYMENT,
            borrowing_id=1,
            money_to_pay=Decimal("10.00"),
        )
        p2 = Payment.objects.create(
            status=PaymentStatus.PAID,
            payment_type=PaymentType.FINE,
            borrowing_id=2,
            money_to_pay=Decimal("5.00"),
        )

        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in resp.data]
        self.assertGreaterEqual(len(ids), 2)
        self.assertGreater(ids[0], ids[1])
        self.assertIn(p1.id, ids)
        self.assertIn(p2.id, ids)

    def test_create_ignores_read_only_fields(self):
        payload = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": 10,
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
        payload = {
            "payment_type": "INVALID",
            "borrowing_id": 1,
            "money_to_pay": "10.00",
        }
        resp = self.client.post(self.list_url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_type", resp.data)

    def test_create_negative_amount_returns_400(self):
        payload = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": 1,
            "money_to_pay": "-0.01",
        }
        resp = self.client.post(self.list_url, data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("money_to_pay", resp.data)

    def test_retrieve_existing(self):
        p = Payment.objects.create(
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.FINE,
            borrowing_id=77,
            money_to_pay=Decimal("0.00"),
        )
        url = reverse("payments-detail", args=[p.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["id"], p.id)
        self.assertEqual(resp.data["payment_type"], PaymentType.FINE)
        self.assertEqual(resp.data["borrowing_id"], 77)
        self.assertEqual(resp.data["money_to_pay"], "0.00")

    def test_retrieve_not_found_returns_404(self):
        url = reverse("payments-detail", args=[999999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed_on_collection(self):
        resp = self.client.put(self.list_url, data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_method_not_allowed_on_detail(self):
        p = Payment.objects.create(
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.PAYMENT,
            borrowing_id=1,
            money_to_pay=Decimal("10.00"),
        )
        detail_url = reverse("payments-detail", args=[p.id])

        resp_patch = self.client.patch(detail_url, data={"status": PaymentStatus.PAID}, format="json")
        resp_put = self.client.put(detail_url, data={"status": PaymentStatus.PAID}, format="json")
        resp_delete = self.client.delete(detail_url)

        self.assertEqual(resp_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(resp_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(resp_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
