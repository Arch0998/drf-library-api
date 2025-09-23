from django.test import TestCase
from django.contrib.auth import get_user_model

from datetime import date, timedelta

from books.models import Book
from borrowings.models import Borrowing


User = get_user_model()


class BorrowingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="denis@example.com", password="12345"
        )

        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover="HARD",
            inventory=5,
            daily_fee=2.5,
        )

        self.borrow_date = date.today()
        self.expected_return_date = self.borrow_date + timedelta(days=7)

    def test_create_borrowing(self):
        expected_return = date.today() + timedelta(days=7)
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_return,
        )
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)
        self.assertIsNone(borrowing.actual_return_date)
        self.assertEqual(
            str(borrowing),
            f"From: {borrowing.borrow_date} "
            f"till: {borrowing.expected_return_date} "
            f"returned: {borrowing.actual_return_date}",
        )

    def test_expected_return_date_constraint(self):
        past_date = date.today() - timedelta(days=1)
        with self.assertRaises(Exception):
            Borrowing.objects.create(
                user=self.user, book=self.book, expected_return_date=past_date
            )

    def test_actual_return_date_constraint(self):
        expected_return = date.today() + timedelta(days=7)
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_return,
        )
        borrowing.actual_return_date = borrowing.borrow_date - timedelta(
            days=1
        )
        with self.assertRaises(Exception):
            borrowing.save()

    def test_unique_active_borrowing_constraint(self):
        expected_return = date.today() + timedelta(days=7)
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_return,
        )
        with self.assertRaises(Exception):
            Borrowing.objects.create(
                user=self.user,
                book=self.book,
                expected_return_date=expected_return,
            )

    def test_allow_new_borrow_after_return(self):
        expected_return = date.today() + timedelta(days=7)
        borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=expected_return,
        )
        borrowing.actual_return_date = date.today()
        borrowing.save()

        new_borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.assertIsNotNone(new_borrowing)
