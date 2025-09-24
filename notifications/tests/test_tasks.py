from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from unittest.mock import patch

from books.models import Book
from borrowings.models import Borrowing
from notifications.tasks import notify_new_borrowing, check_overdue_borrowings


@pytest.mark.django_db
def test_notify_new_borrowing_sends_message():
    User = get_user_model()
    user = User.objects.create_user(email="test@example.com", password="pass")
    book = Book.objects.create(
        title="Test Book",
        author="Test Author",
        cover="HARD",
        inventory=5,
        daily_fee=1.00,
    )
    borrowing = Borrowing.objects.create(
        user=user,
        book=book,
        expected_return_date=date.today() + timedelta(days=7),
    )
    with patch("notifications.tasks.send_telegram_message") as mock_send:
        mock_send.return_value = True
        notify_new_borrowing(borrowing.id)
        mock_send.assert_called_once()


@pytest.mark.django_db
def test_check_overdue_borrowings_sends_message():
    User = get_user_model()
    user = User.objects.create_user(email="test2@example.com", password="pass")
    book = Book.objects.create(
        title="Test Book 2",
        author="Test Author",
        cover="SOFT",
        inventory=3,
        daily_fee=2.00,
    )
    borrow_date = date.today() - timedelta(days=5)
    expected_return_date = date.today() - timedelta(days=1)

    overdue_borrowing = Borrowing.objects.create(
        user=user,
        book=book,
        borrow_date=borrow_date,
        expected_return_date=expected_return_date,
    )
    with patch("notifications.tasks.send_telegram_message") as mock_send:
        mock_send.return_value = True
        check_overdue_borrowings()
        assert mock_send.called
