from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingCreateSerializer,
)

User = get_user_model()


class BorrowingSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="12345"
        )
        self.book = Book.objects.create(
            title="Book",
            author="Author",
            cover="HARD",
            inventory=2,
            daily_fee=1.0,
        )
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=3),
        )

    def test_borrowing_serializer_data(self):
        serializer = BorrowingSerializer(self.borrowing)
        data = serializer.data
        self.assertEqual(data["id"], self.borrowing.id)
        self.assertEqual(data["borrow_date"], str(self.borrowing.borrow_date))

    def test_borrowing_create_serializer_valid(self):
        data = {
            "expected_return_date": str(date.today() + timedelta(days=5)),
            "book": self.book.id,
        }
        serializer = BorrowingCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_borrowing_create_serializer_invalid_inventory(self):
        self.book.inventory = 0
        self.book.save()
        data = {
            "expected_return_date": str(date.today() + timedelta(days=5)),
            "book": self.book.id,
        }
        serializer = BorrowingCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("book", serializer.errors)
