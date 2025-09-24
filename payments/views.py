import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import mixins, viewsets, status
from rest_framework.views import APIView

from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentDetailSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List payments",
        description="Returns a list of payments ordered by ID descending.",
        responses=PaymentSerializer,
    ),
    retrieve=extend_schema(
        summary="Retrieve a payment",
        description="Returns a single payment by its ID.",
        responses=PaymentSerializer,
    ),
    create=extend_schema(
        summary="Create a payment",
        description="Creates a new payment. session_url"
        "and session_id are read-only.",
        request=PaymentSerializer,
        responses=PaymentSerializer,
    ),
)
class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    queryset = Payment.objects.select_related("borrowing")
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentSerializer

    def get_queryset(self):
        queryset = Payment.objects.select_related("borrowing")
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)
        return queryset


class PaymentSuccessView(APIView):
    """Handle successful payment callback from Stripe"""

    def _update_payment_status(self, session_id, is_test=False):
        """Common logic for updating payment status"""
        try:
            payment = Payment.objects.get(session_id=session_id)
            payment.status = "PAID"
            payment.save()

            message = (
                "Payment status updated to PAID (TEST MODE)"
                if is_test
                else "Payment successful!"
            )

            return Response(
                {
                    "message": message,
                    "payment_id": payment.id,
                    "status": payment.status,
                }
            )
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    def get(self, request):
        session_id = request.GET.get("session_id")

        if not session_id:
            return Response(
                {"error": "Session ID not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == "paid":
                return self._update_payment_status(session_id)
            else:
                return Response(
                    {"message": "Payment not completed yet"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PaymentCancelView(APIView):
    """Handle cancelled payment from Stripe"""

    def get(self, request):
        return Response(
            {
                "message": "Payment was cancelled."
                " You can complete the payment later,"
                " but the session is available"
                " for only 24 hours."
            }
        )


class PaymentTestSuccessView(APIView):
    """Test endpoint to simulate successful payment - FOR DEVELOPMENT ONLY"""

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        session_id = request.data.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success_view = PaymentSuccessView()
        return success_view._update_payment_status(session_id, is_test=True)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    """Handle Stripe webhook events"""

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

        if endpoint_secret:
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, endpoint_secret
                )
            except ValueError:
                return HttpResponse("Invalid payload", status=400)
            except stripe.error.SignatureVerificationError:
                return HttpResponse("Invalid signature", status=400)
        else:
            try:
                import json

                event = json.loads(payload.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                return HttpResponse("Invalid payload", status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            session_id = session["id"]

            try:
                payment = Payment.objects.get(session_id=session_id)
                if session["payment_status"] == "paid":
                    payment.status = "PAID"
                    payment.save()
            except Payment.DoesNotExist:
                pass

        return HttpResponse(status=200)
