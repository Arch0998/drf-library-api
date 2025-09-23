from celery import shared_task
from django.utils import timezone

from notifications.telegram_helper import send_telegram_message
from borrowings.models import Borrowing


@shared_task
def notify_new_borrowing(borrowing_id):
    try:
        borrowing = Borrowing.objects.select_related("book", "user").get(
            id=borrowing_id
        )
        message = (
            f"New borrowing created!\n"
            f"{borrowing.user}\n"
            f"Book: {borrowing.book.title}\n"
            f"Borrowed: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )
        send_telegram_message(message)
    except Borrowing.DoesNotExist:
        pass


@shared_task
def check_overdue_borrowings():
    today = timezone.now().date()
    overdues = Borrowing.objects.filter(
        expected_return_date__lte=today, actual_return_date__isnull=True
    ).select_related("book", "user")
    if overdues.exists():
        for b in overdues:
            msg = (
                f"Overdue borrowing!\n"
                f"{b.user}\n"
                f"Book: {b.book.title}\n"
                f"Borrowed: {b.borrow_date}\n"
                f"Expected return: {b.expected_return_date}\n"
                f"Status: Not returned!"
            )
            send_telegram_message(msg)
    else:
        send_telegram_message("✅ No borrowings overdue today!")
