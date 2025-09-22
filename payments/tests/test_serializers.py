from decimal import Decimal
from django.test import TestCase
from payments.models import Payment, PaymentStatus, PaymentType
from payments.serializers import PaymentSerializer


class PaymentSerializerTests(TestCase):
    def test_create_payment_valid(self):
        data = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": 123,
            "money_to_pay": "15.50",
        }
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        obj = serializer.save()

        self.assertIsInstance(obj, Payment)
        self.assertIsNotNone(obj.id)
        self.assertEqual(obj.status, PaymentStatus.PENDING)
        self.assertEqual(obj.payment_type, PaymentType.PAYMENT)
        self.assertEqual(obj.borrowing_id, 123)
        self.assertEqual(obj.money_to_pay, Decimal("15.50"))
        self.assertIsNone(obj.session_id)
        self.assertIsNone(obj.session_url)

    def test_invalid_status(self):
        data = {
            "status": "INVALID",
            "payment_type": PaymentType.FINE,
            "borrowing_id": 1,
            "money_to_pay": "10.00",
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_invalid_payment_type(self):
        data = {
            "payment_type": "INVALID",
            "borrowing_id": 1,
            "money_to_pay": "10.00",
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("payment_type", serializer.errors)

    def test_negative_amount(self):
        data = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": 1,
            "money_to_pay": "-0.01",
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("money_to_pay", serializer.errors)

    def test_missing_money_to_pay(self):
        data = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": 1,
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("money_to_pay", serializer.errors)
