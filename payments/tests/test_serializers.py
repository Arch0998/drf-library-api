from decimal import Decimal
from django.test import TestCase
from payments.models import Payment, PaymentStatus, PaymentType
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
)
from borrowings.models import Borrowing
from books.models import Book
from django.contrib.auth import get_user_model
from datetime import date, timedelta


User = get_user_model()


class PaymentSerializerTests(TestCase):
    def _create_user(self):
        return get_user_model().objects.create_user(
            email="ser@test.com", password="testpass123"
        )

    def _create_book(self):
        return Book.objects.create(
            title="S Book",
            author="Author",
            cover="HARD",
            inventory=5,
            daily_fee=Decimal("1.00"),
        )

    def _create_borrowing(self):
        return Borrowing.objects.create(
            user=self._create_user(),
            book=self._create_book(),
            expected_return_date=date.today() + timedelta(days=3),
        )

    def test_create_payment_valid(self):
        borrowing = self._create_borrowing()
        data = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing": borrowing.id,
            "money_to_pay": "15.50",
        }
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        obj = serializer.save()

        self.assertIsInstance(obj, Payment)
        self.assertIsNotNone(obj.id)
        self.assertEqual(obj.status, PaymentStatus.PENDING)
        self.assertEqual(obj.payment_type, PaymentType.PAYMENT)
        self.assertEqual(obj.borrowing_id, borrowing.id)
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

    def test_missing_money_to_pay(self):
        data = {
            "payment_type": PaymentType.PAYMENT,
            "borrowing_id": 1,
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("money_to_pay", serializer.errors)


class PaymentListSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testlist@example.com", password="testpass123"
        )
        self.book = Book.objects.create(
            title="Test Book List",
            author="Test Author",
            cover="HARD",
            inventory=5,
            daily_fee=Decimal("2.50"),
        )
        self.borrowing = Borrowing.objects.create(
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )
        self.payment = Payment.objects.create(
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.PAYMENT,
            borrowing=self.borrowing,
            money_to_pay=Decimal("35.00"),
        )

    def test_payment_list_serializer_fields(self):
        """Test PaymentListSerializer contains only expected fields"""
        serializer = PaymentListSerializer(instance=self.payment)
        expected_fields = {
            "id",
            "status",
            "payment_type",
            "borrowing",
            "money_to_pay",
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_payment_list_serializer_borrowing_as_id(self):
        """Test PaymentListSerializer returns borrowing as ID not nested object"""
        serializer = PaymentListSerializer(instance=self.payment)
        # borrowing should be just the ID, not nested data
        self.assertEqual(serializer.data["borrowing"], self.borrowing.id)
        self.assertIsInstance(serializer.data["borrowing"], int)
