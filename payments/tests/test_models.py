from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from payments.models import Payment, PaymentStatus, PaymentType


class PaymentModelTests(TestCase):
    def create_payment(
        self,
        *,
        borrowing_id: int = 1,
        status: str = PaymentStatus.PENDING,
        payment_type: str = PaymentType.PAYMENT,
        money_to_pay: Decimal = Decimal("10.00"),
        session_url: str | None = None,
        session_id: str | None = None,
    ) -> Payment:
        return Payment.objects.create(
            borrowing_id=borrowing_id,
            status=status,
            payment_type=payment_type,
            money_to_pay=money_to_pay,
            session_url=session_url,
            session_id=session_id,
        )

    def test_create_payment_success(self):
        p = self.create_payment()
        self.assertIsNotNone(p.id)
        self.assertEqual(p.status, PaymentStatus.PENDING)
        self.assertEqual(p.payment_type, PaymentType.PAYMENT)
        self.assertEqual(p.borrowing_id, 1)
        self.assertEqual(p.money_to_pay, Decimal("10.00"))
        self.assertIsNone(p.session_url)
        self.assertIsNone(p.session_id)

    def test_money_to_pay_non_negative_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_payment(money_to_pay=Decimal("-0.01"))

        # zero is allowed
        p = self.create_payment(money_to_pay=Decimal("0.00"))
        self.assertEqual(p.money_to_pay, Decimal("0.00"))

    def test_unique_pending_per_borrowing_and_type_constraint(self):
        # First pending for (borrowing_id=1, PAYMENT)
        self.create_payment(
            borrowing_id=1,
            payment_type=PaymentType.PAYMENT,
            status=PaymentStatus.PENDING,
        )

        # Second pending with same pair should fail
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_payment(
                    borrowing_id=1,
                    payment_type=PaymentType.PAYMENT,
                    status=PaymentStatus.PENDING,
                )

        # But a PAID for same pair is allowed
        p_paid = self.create_payment(
            borrowing_id=1,
            payment_type=PaymentType.PAYMENT,
            status=PaymentStatus.PAID,
        )
        self.assertEqual(p_paid.status, PaymentStatus.PAID)

        # And a PENDING with a different type is allowed
        p_other_type = self.create_payment(
            borrowing_id=1,
            payment_type=PaymentType.FINE,
            status=PaymentStatus.PENDING,
        )
        self.assertEqual(p_other_type.payment_type, PaymentType.FINE)

    def test_choices_validation_with_full_clean(self):
        p = Payment(
            borrowing_id=2,
            status="INVALID",
            payment_type=PaymentType.PAYMENT,
            money_to_pay=Decimal("5.00"),
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

        p2 = Payment(
            borrowing_id=2,
            status=PaymentStatus.PENDING,
            payment_type="INVALID",
            money_to_pay=Decimal("5.00"),
        )
        with self.assertRaises(ValidationError):
            p2.full_clean()

    def test_session_fields_optional(self):
        p = self.create_payment(session_url=None, session_id=None)
        self.assertIsNone(p.session_url)
        self.assertIsNone(p.session_id)

    def test_str_representation(self):
        p = self.create_payment(
            borrowing_id=5,
            status=PaymentStatus.PENDING,
            payment_type=PaymentType.FINE,
            money_to_pay=Decimal("12.34"),
        )
        s = str(p)
        self.assertIn("status=PENDING", s)
        self.assertIn("type=FINE", s)
        self.assertIn("borrowing_id=5", s)
        self.assertIn("amount=12.34 USD", s)
