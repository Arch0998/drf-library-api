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

    def validate_status(self, value: str) -> str:
        if value not in dict(PaymentStatus.choices):
            raise serializers.ValidationError("Invalid status")
        return value

    def validate_payment_type(self, value: str) -> str:
        if value not in dict(PaymentType.choices):
            raise serializers.ValidationError("Invalid payment_type")
        return value

    def validate_money_to_pay(self, value: Decimal) -> Decimal:
        if value is None:
            raise serializers.ValidationError("money_to_pay is required")
        if value < 0:
            raise serializers.ValidationError(
                "money_to_pay must be non-negative"
            )
        return value


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
