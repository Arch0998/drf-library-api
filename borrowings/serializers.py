from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from notifications.tasks import notify_new_borrowing
from users.serializers import UserSerializer


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
        )
        read_only_fields = ("id", "borrow_date", "actual_return_date")


class BorrowingListSerializer(serializers.ModelSerializer):
    payments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    book = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="title",
    )
    user = serializers.SlugRelatedField(
        many=False,
        read_only=True,
        slug_field="email",
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "payments",
        )
        read_only_fields = (
            "id",
            "borrow_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingDetailSerializer(BorrowingListSerializer):
    book = BookSerializer()
    user = UserSerializer()


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("expected_return_date", "book")

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Borrowing:
        book = validated_data.pop("book")
        book.inventory -= 1
        book.save()
        borrowing = Borrowing.objects.create(book=book, **validated_data)
        notify_new_borrowing.delay(borrowing.id)
        return borrowing

    def validate_book(self, value: Book) -> Book:
        if value.inventory <= 0:
            raise serializers.ValidationError("Not enough books")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        Borrowing.validate_expected_return_date(
            expected_return_date=attrs["expected_return_date"],
            borrow_date=timezone.now().date(),
            error_to_raise=serializers.ValidationError,
        )
        return attrs
