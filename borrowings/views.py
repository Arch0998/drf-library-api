from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingCreateSerializer,
    BorrowingDetailSerializer,
    BorrowingListSerializer,
    BorrowingSerializer,
)
from payments.models import Payment, PaymentType
from payments.stripe_helper import create_stripe_session


FINE_MULTIPLIER = 2


@extend_schema_view(
    list=extend_schema(
        summary="List Borrowings",
        description="Staff see all borrowings,"
        " users see only their own. Supports filters.",
        tags=["Borrowings"],
    ),
    retrieve=extend_schema(
        summary="Borrowing Details",
        description="Staff can view any borrowing, users only their own.",
        tags=["Borrowings"],
    ),
    create=extend_schema(
        summary="Create Borrowing",
        description="Create a borrowing."
        " A Stripe payment session is generated.",
        tags=["Borrowings"],
    ),
    return_book=extend_schema(
        summary="Return Borrowing",
        description="Return a borrowed book and increase inventory.",
        tags=["Borrowings"],
    ),
)
class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user", "book", "borrow_date", "actual_return_date"]

    def get_serializer_class(self) -> type:
        if self.action == "list":
            return BorrowingListSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        if self.action == "create":
            return BorrowingCreateSerializer
        return BorrowingSerializer

    def perform_create(self, serializer: BorrowingCreateSerializer) -> None:
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

    def get_queryset(self) -> Any:
        queryset = Borrowing.objects.all().select_related("book", "user")
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset

    @action(
        detail=True,
        methods=["post"],
        url_path="return",
        permission_classes=[IsAuthenticated],
    )
    def return_book(self, request: Request, pk: str = None) -> Response:
        borrowing = self.get_object()

        if not request.user.is_staff and borrowing.user != request.user:
            return Response(
                {"detail": "You don't have permission to return this book."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "This book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.now().date()

        with transaction.atomic():
            borrowing.actual_return_date = timezone.now().date()
            borrowing.save()
            borrowing.book.inventory += 1
            borrowing.book.save()

        if today > borrowing.expected_return_date:
            fine_amount = self.calculate_fine(borrowing, today)

            try:
                session_data = create_stripe_session(
                    borrowing=borrowing,
                    payment_type=PaymentType.FINE,
                    request=request,
                    fine_amount=fine_amount,
                )

                Payment.objects.create(
                    borrowing=borrowing,
                    session_id=session_data["session_id"],
                    session_url=session_data["session_url"],
                    money_to_pay=fine_amount,
                    payment_type=PaymentType.FINE,
                    status="PENDING",
                )

                serializer = self.get_serializer(borrowing)
                return Response(
                    {
                        "borrowing": serializer.data,
                        "message": "Book returned successfully, "
                        " but you have a fine to pay",
                        "days_overdue": (
                            today - borrowing.expected_return_date
                        ).days,
                        "fine_amount": str(fine_amount),
                        "payment_url": session_data["session_url"],
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception as e:
                serializer = self.get_serializer(borrowing)
                return Response(
                    {
                        "borrowing": serializer.data,
                        "message": "Book returned successfully,"
                        " but error creating fine payment",
                        "error": str(e),
                        "days_overdue": (
                            today - borrowing.expected_return_date
                        ).days,
                        "fine_amount": str(fine_amount),
                    },
                    status=status.HTTP_200_OK,
                )

        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def calculate_fine(
        self, borrowing: Borrowing, actual_return_date: Any
    ) -> Decimal:
        days_overdue = (
            actual_return_date - borrowing.expected_return_date
        ).days
        daily_fee = borrowing.book.daily_fee

        fine_amount = (
            Decimal(days_overdue) * daily_fee * Decimal(FINE_MULTIPLIER)
        )
        return fine_amount
