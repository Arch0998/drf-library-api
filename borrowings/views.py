from django.db.models import F

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.utils import timezone

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingReturnSerializer,
)


class BorrowingOutOfStock(APIException):
    status_code = 204
    default_detail = "Book is out of stock."
    default_code = "no_inventory"


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get("user_id")
        is_active = self.request.query_params.get("is_active")

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            else:
                queryset = queryset.filter(actual_return_date__isnull=False)
        return queryset

    def perform_create(self, serializer):
        book = serializer.validated_data["book"]
        if book.inventory <= 0:
            raise BorrowingOutOfStock()

        borrowing = serializer.save(user=self.request.user)

        borrowing.book.inventory = F("inventory") - 1
        borrowing.book.save(update_fields=["inventory"])

    @action(detail=True, methods=["post"], url_path="return")
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date:
            return Response(
                {"detail": "Book already returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing.actual_return_date = timezone.now().date()
        borrowing.save()

        borrowing.book.inventory = F("inventory") + 1
        borrowing.book.save(update_fields=["inventory"])

        serializer = BorrowingReturnSerializer(borrowing)
        return Response(serializer.data, status=status.HTTP_200_OK)
