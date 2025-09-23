from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingCreateSerializer,
    BorrowingDetailSerializer,
    BorrowingListSerializer,
    BorrowingSerializer,
)
from payments.models import Payment, PaymentType
from payments.stripe_helper import create_stripe_session

@extend_schema_view(
    list=extend_schema(
        summary="List Borrowings",
        description="Staff see all borrowings, users see only their own. Supports filters.",
        tags=["Borrowings"],
    ),
    retrieve=extend_schema(
        summary="Borrowing Details",
        description="Staff can view any borrowing, users only their own.",
        tags=["Borrowings"],
    ),
    create=extend_schema(
        summary="Create Borrowing",
        description="Create a borrowing. A Stripe payment session is generated.",
        tags=["Borrowings"],
    ),
)
class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        Borrowing.objects.all()
        .select_related("book", "user")
        .order_by("-borrow_date")
    )
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "book", "borrow_date", "actual_return_date"]

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        return BorrowingSerializer

    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)

        session_data = create_stripe_session(
            borrowing=borrowing,
            payment_type=PaymentType.PAYMENT,
            request=self.request,
        )

        Payment.objects.create(
            borrowing=borrowing,
            session_id=session_data["session_id"],
            session_url=session_data["session_url"],
            money_to_pay=session_data["amount"],
            payment_type=PaymentType.PAYMENT,
            status="PENDING",
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset
