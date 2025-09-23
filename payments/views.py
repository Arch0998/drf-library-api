import stripe
import logging
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

            payment = Payment.objects.get(session_id=session_id)

            if session.payment_status == "paid":
                payment.status = "PAID"
                payment.save()

                return Response(
                    {
                        "message": "Payment successful!",
                        "payment_id": payment.id,
                    }
                )
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

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Handle Stripe webhook events"""
    
    permission_classes = []
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            logger.warning("No Stripe signature header found")
            return HttpResponse(status=400)
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            logger.info(f"Received Stripe webhook event: {event['type']}")
            
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            return HttpResponse(status=400)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_successful_payment(session)
            
        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            self.handle_expired_session(session)
            
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return HttpResponse(status=200)
    
    def handle_successful_payment(self, session):
        """Handle successful payment completion"""
        try:
            session_id = session['id']
            payment = Payment.objects.get(session_id=session_id)
            
            if payment.status != 'PAID':
                payment.status = 'PAID'
                payment.save()
                logger.info(f"Payment {payment.id} marked as PAID via webhook")

            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for session {session_id}")
        except Exception as e:
            logger.error(f"Error handling successful payment: {e}")
    
    def handle_expired_session(self, session):
        """Handle expired checkout session"""
        try:
            session_id = session['id']
            payment = Payment.objects.get(session_id=session_id)
            
            if payment.status == 'PENDING':
                payment.status = 'EXPIRED'
                payment.save()
                logger.info(f"Payment session {payment.id} expired")
                
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for expired session {session_id}")
        except Exception as e:
            logger.error(f"Error handling expired session: {e}")
