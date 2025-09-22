from rest_framework import serializers

from borrowings.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = "__all__"
        read_only_fields = ("user", "borrow_date", "actual_return_date")

    def validate(self, attrs):
        book = attrs["book"]
        if book.inventory <= 0:
            raise serializers.ValidationError(
                {"book": "This book is out of stock."}
            )
        return attrs


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "actual_return_date", "book", "user")