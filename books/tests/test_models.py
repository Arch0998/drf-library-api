from django.test import TestCase
from django.core.exceptions import ValidationError
from books.models import Book


class BookModelTest(TestCase):
    def test_daily_fee_cannot_be_negative(self):
        book = Book(
            title="Test Book",
            author="Test Author",
            cover="HARD",
            inventory=10,
            daily_fee=-1.01,
        )
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_inventory_cannot_be_negative(self):
        book = Book(
            title="Test Book",
            author="Test Author",
            cover="HARD",
            inventory=-5,
            daily_fee=10,
        )
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_valid_book_can_be_saved(self):
        book = Book(
            title="Test Book",
            author="Test Author",
            cover="HARD",
            inventory=5,
            daily_fee=2.5,
        )
        book.full_clean()
        book.save()
        self.assertEqual(Book.objects.count(), 1)
