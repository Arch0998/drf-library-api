import json
from decimal import Decimal
from datetime import date, timedelta

from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock

from payments.models import Payment, PaymentStatus, PaymentType
from books.models import Book
from borrowings.models import Borrowing


class StripeIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.webhook_url = reverse("payments:webhook")
        self.test_success_url = reverse("payments:test-success")

        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )

        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="HARD",
            inventory=10,
            daily_fee=Decimal("1.50"),
        )

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=5),
        )

        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            session_id="cs_test_session_id_123",
            session_url="https://checkout.stripe.com/pay/test",
            money_to_pay=Decimal("15.00"),
            payment_type=PaymentType.PAYMENT,
            status="PENDING",
        )

    @patch('payments.views.notify_successful_payment.delay')
    @patch('django.db.transaction.on_commit', side_effect=lambda func: func())
    def test_stripe_webhook_successful_payment(self, mock_on_commit, mock_notify):
        """Test Stripe webhook handles successful payment correctly"""
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_session_id_123",
                    "payment_status": "paid",
                    "amount_total": 1500,  # in cents
                    "currency": "usd",
                }
            }
        }
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(webhook_payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake_signature"
        )
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check payment status was updated
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "PAID")
        
        # Check notification was triggered
        mock_notify.assert_called_once_with(self.payment.id)

    def test_stripe_webhook_payment_not_found(self):
        """Test webhook gracefully handles non-existent payment"""
        webhook_payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_nonexistent_session_id",
                    "payment_status": "paid",
                }
            }
        }
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(webhook_payload),
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake_signature"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('payments.views.notify_successful_payment.delay')
    @patch('django.db.transaction.on_commit', side_effect=lambda func: func())
    def test_payment_test_success_view(self, mock_on_commit, mock_notify):
        """Test PaymentTestSuccessView updates payment status correctly"""
        self.client.force_authenticate(user=self.user)
        
        payload = {
            "session_id": "cs_test_session_id_123"
        }
        
        response = self.client.post(
            self.test_success_url,
            data=payload,
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Payment status updated to PAID (TEST MODE)", response.data["message"])
        self.assertEqual(response.data["payment_id"], self.payment.id)
        self.assertEqual(response.data["status"], "PAID")
        
        # Check payment was updated in database
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "PAID")
        
        # Check notification was triggered
        mock_notify.assert_called_once_with(self.payment.id)

    def test_payment_test_success_view_requires_authentication(self):
        """Test that PaymentTestSuccessView requires authentication"""
        payload = {
            "session_id": "cs_test_session_id_123"
        }
        
        response = self.client.post(
            self.test_success_url,
            data=payload,
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payment_test_success_view_missing_session_id(self):
        """Test PaymentTestSuccessView validates required session_id"""
        self.client.force_authenticate(user=self.user)
        
        # Empty payload
        response = self.client.post(
            self.test_success_url,
            data={},
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "session_id is required")

    def test_payment_test_success_view_nonexistent_payment(self):
        """Test PaymentTestSuccessView handles non-existent payment"""
        self.client.force_authenticate(user=self.user)
        
        payload = {
            "session_id": "cs_nonexistent_session_id"
        }
        
        response = self.client.post(
            self.test_success_url,
            data=payload,
            format="json"
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Payment not found")