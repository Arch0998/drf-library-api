from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from books.models import Book
from borrowings.models import Borrowing

User = get_user_model()

class BorrowingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="denis", password="12345")
        self.book = Book.objects.create(title="Test Book")

    def test_create_borrowing(self):
        expected_return = date.today() + timedelta(days=7)
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_return
        )
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.actual_return_date, None)
        self.assertEqual(borrowing.expected_return_date, expected_return)
        self.assertEqual(str(borrowing), f"{self.user} borrowed {self.book} on {borrowing.borrow_date}")

    def test_expected_return_date_constraint(self):
        expected_return = date.today() - timedelta(days=1)
        with self.assertRaises(Exception):
            Borrowing.objects.create(
                user=self.user,
                book=self.book,
                expected_return_date=expected_return
            )

    def test_unique_active_borrowing_constraint(self):
        expected_return = date.today() + timedelta(days=7)
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_return
        )

        with self.assertRaises(Exception):
            Borrowing.objects.create(
                user=self.user,
                book=self.book,
                expected_return_date=expected_return
            )

    def test_actual_return_date_constraint(self):
        expected_return = date.today() + timedelta(days=7)
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_return
        )
        borrowing.actual_return_date = borrowing.borrow_date - timedelta(days=1)
        with self.assertRaises(Exception):
            borrowing.save()