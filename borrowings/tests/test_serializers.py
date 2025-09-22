from django.test import TestCase
from books.models import Book
from users.models import User
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingReturnSerializer,
)
from datetime import date, timedelta
from rest_framework.exceptions import ValidationError


class BorrowingSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="12345"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            cover="HARD",
            inventory=5,
            daily_fee=2.5,
        )
        self.borrow_date = date.today()
        self.expected_return_date = self.borrow_date + timedelta(days=7)

    def test_borrowing_serializer_valid(self):
        data = {
            "book": self.book.id,
            "user": self.user.id,
            "expected_return_date": self.expected_return_date,
        }
        serializer = BorrowingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_borrowing_serializer_inventory_zero(self):
        self.book.inventory = 0
        self.book.save()
        data = {
            "book": self.book.id,
            "user": self.user.id,
            "expected_return_date": self.expected_return_date,
        }
        serializer = BorrowingSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class BorrowingReturnSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="12345"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            cover="HARD",
            inventory=5,
            daily_fee=2.5,
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

    def test_return_serializer_update_actual_return_date(self):
        data = {"actual_return_date": date.today()}
        serializer = BorrowingReturnSerializer(
            instance=self.borrowing, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        borrowing = serializer.save()
        self.assertEqual(
            borrowing.actual_return_date, data["actual_return_date"]
        )
