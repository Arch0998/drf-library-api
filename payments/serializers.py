from rest_framework import serializers
from payments.models import Payment, PaymentStatus, PaymentType
from borrowings.models import Borrowing


class PaymentSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.PrimaryKeyRelatedField(
        source="borrowing",
        queryset=Borrowing.objects.all(),
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "payment_type",
            "borrowing_id",
            "session_url",
            "session_id",
            "money_to_pay",
        ]
        read_only_fields = ["id", "session_url", "session_id"]

    def validate_status(self, value):
        if value not in dict(PaymentStatus.choices):
            raise serializers.ValidationError("Invalid status")
        return value

    def validate_payment_type(self, value):
        if value not in dict(PaymentType.choices):
            raise serializers.ValidationError("Invalid payment_type")
        return value

    def validate_money_to_pay(self, value):
        if value is None:
            raise serializers.ValidationError("money_to_pay is required")
        if value < 0:
            raise serializers.ValidationError("money_to_pay must be non-negative")
        return value
