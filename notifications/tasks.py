from celery import shared_task
from django.utils import timezone

from borrowings.models import Borrowing
from notifications.telegram_helper import send_telegram_message


@shared_task
def notify_new_borrowing(borrowing_id: int) -> None:
    try:
        borrowing = Borrowing.objects.select_related("book", "user").get(
            id=borrowing_id
        )
        message = (
            f"📚 New Borrowing Created!\n"
            f"👤 User: {borrowing.user.get_full_name()}\n"
            f"📖 Book: {borrowing.book.title}\n"
            f"📅 Borrowed: {borrowing.borrow_date}\n"
            f"📅 Expected Return: {borrowing.expected_return_date}\n"
            f"💰 Daily Fee: ${borrowing.book.daily_fee}"
        )
        send_telegram_message(message)
    except Borrowing.DoesNotExist:
        pass


@shared_task
def notify_successful_payment(payment_id: int) -> None:
    try:
        from payments.models import Payment

        payment = Payment.objects.select_related(
            "borrowing__book", "borrowing__user"
        ).get(id=payment_id)

        borrowing = payment.borrowing
        message = (
            f"💰 Payment Completed!\n"
            f"👤 User: {borrowing.user.get_full_name()}\n"
            f"📚 Book: {borrowing.book.title}\n"
            f"💵 Amount: ${payment.money_to_pay}\n"
            f"💳 Payment Type: {payment.payment_type}\n"
            f"✅ Status: {payment.status}\n"
            f"📅 Borrowed: {borrowing.borrow_date}\n"
            f"📅 Expected Return: {borrowing.expected_return_date}"
        )
        send_telegram_message(message)
    except Exception:
        pass


@shared_task
def check_overdue_borrowings() -> None:
    today = timezone.now().date()
    overdues = Borrowing.objects.filter(
        expected_return_date__lte=today, actual_return_date__isnull=True
    ).select_related("book", "user")

    if overdues.exists():
        for borrowing in overdues:
            days_overdue = (today - borrowing.expected_return_date).days
            message = (
                f"⚠️ Overdue Borrowing Alert!\n"
                f"👤 User: {borrowing.user.get_full_name()}\n"
                f"📚 Book: {borrowing.book.title}\n"
                f"📅 Borrowed: {borrowing.borrow_date}\n"
                f"📅 Expected Return: {borrowing.expected_return_date}\n"
                f"⏰ Days Overdue: {days_overdue}\n"
                f"❌ Status: Not returned!\n"
                f"💸 Daily Fee: ${borrowing.book.daily_fee}"
            )
            send_telegram_message(message)
    else:
        send_telegram_message("✅ No borrowings overdue today!")
