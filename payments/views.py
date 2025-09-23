import stripe
from django.conf import settings
from drf_spectacular.utils import extend_schema_view, extend_schema
from requests import Response
from rest_framework import mixins, viewsets, status
from rest_framework.views import APIView

from payments.models import Payment, PaymentStatus
from payments.serializers import PaymentSerializer


stripe.api_key = settings.STRIPE_SECRET_KEY
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
    """
    ViewSet for Payment:
    - list: GET /payments/
    - create: POST /payments/
    - retrieve: GET /payments/{id}/
    """

    queryset = Payment.objects.all().order_by("-id")
    serializer_class = PaymentSerializer


class PaymentSuccessView(APIView):
    """Handle successful Stripe payment"""

    def get(self, request):
        session_id = request.GET.get('session_id')

        if not session_id:
            return Response(
                {'error': 'Session ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)

            # Find payment in database
            payment = Payment.objects.get(session_id=session_id)

            # Check if payment was successful
            if session.payment_status == 'paid':
                payment.status = PaymentStatus.PAID
                payment.save()

                return Response({
                    'message': 'Payment successful!',
                    'payment_id': payment.id,
                    'amount': str(payment.money_to_pay)
                })
            else:
                return Response(
                    {'error': 'Payment was not completed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            return Response(
                {'error': f'Stripe error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentCancelView(APIView):
    """Handle cancelled Stripe payment"""

    def get(self, request):
        return Response({
            'message': 'Payment was cancelled. You can complete the payment later.',
            'note': 'The payment session is available for 24 hours.'
        })
