from rest_framework import serializers

from borrowings.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "user", "book", "borrow_date", "actual_return_date")
        read_only_fields = ("id", "user", "borrow_date")

    def validate(self, attrs):
        book = attrs["book"]
        borrow_date = attrs.get("borrow_date")
        expected_return_date = attrs.get("expected_return_date")

        if book.inventory <= 0:
            raise serializers.ValidationError(
                {"book": "This book is out of stock."}
            )

        if (
            borrow_date
            and expected_return_date
            and expected_return_date <= borrow_date
        ):
            raise serializers.ValidationError(
                {
                    "expected_return_date":
                        "Expected return date must be after borrow date."
                }
            )

        return attrs


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "actual_return_date", "book", "user")

    def validate(self, attrs):
        actual_return_date = attrs.get("actual_return_date")
        borrow_date = self.instance.borrow_date if self.instance else None

        if (
            borrow_date
            and actual_return_date
            and actual_return_date < borrow_date
        ):
            raise serializers.ValidationError(
                {
                    "actual_return_date":
                        "Actual return date cannot be before borrow date."
                }
            )

        return attrs
