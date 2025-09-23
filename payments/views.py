from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import mixins, viewsets
from payments.models import Payment
from payments.serializers import PaymentSerializer


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

    queryset = Payment.objects.select_related("borrowing")
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = Payment.objects.select_related("borrowing")
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(borrowing__user=user)
        return queryset
