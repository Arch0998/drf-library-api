import stripe
from django.conf import settings
from drf_spectacular.utils import extend_schema_view, extend_schema
from requests import Response
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
        session_id = request.GET.get('session_id')

        if not session_id:
            return Response(
                {"error": "Session ID not provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)

            payment = Payment.objects.get(session_id=session_id)

            if session.payment_status == 'paid':
                payment.status = 'PAID'
                payment.save()

                return Response({
                    "message": "Payment successful!",
                    "payment_id": payment.id
                })
            else:
                return Response({
                    "message": "Payment not completed yet"
                }, status=status.HTTP_400_BAD_REQUEST)

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentCancelView(APIView):
    """Handle cancelled payment from Stripe"""

    def get(self, request):
        return Response({
            "message": "Payment was cancelled. You can complete the payment later, but the session is available for only 24 hours."
        })

