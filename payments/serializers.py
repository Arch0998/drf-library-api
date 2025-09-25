from decimal import Decimal

from rest_framework import serializers

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer
from payments.models import Payment, PaymentStatus, PaymentType


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = serializers.PrimaryKeyRelatedField(
        queryset=Borrowing.objects.all(),
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "payment_type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        ]
        read_only_fields = ["id", "session_url", "session_id"]


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing = serializers.SlugRelatedField(read_only=True, slug_field="id")

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "payment_type",
            "borrowing",
            "money_to_pay",
        )


class PaymentDetailSerializer(PaymentSerializer):
    borrowing = BorrowingSerializer(
        read_only=True,
    )
