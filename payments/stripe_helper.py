import stripe
from django.conf import settings
from django.urls import reverse
from decimal import Decimal

from payments.models import PaymentType

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(
    borrowing, payment_type=PaymentType.PAYMENT, request=None, fine_amount=None
):
    """
    Create a Stripe checkout session for a borrowing.

    Args:
        borrowing: Borrowing instance
        payment_type: PaymentType (PAYMENT or FINE)
        request: Django request object for building absolute URIs
        fine_amount: Decimal amount for FINE payments (required for FINE)

    Returns:
        dict: Contains session_id and session_url and amount
    """
    if payment_type == PaymentType.PAYMENT:
        borrow_days = (
            borrowing.expected_return_date - borrowing.borrow_date
        ).days
        if borrow_days <= 0:
            borrow_days = 1
        total_price = borrowing.book.daily_fee * Decimal(borrow_days)
        description = f"Book rental for {borrow_days} days"
        product_name = f"Book Rental: {borrowing.book.title}"

    elif payment_type == PaymentType.FINE:
        if fine_amount is None:
            raise ValueError("fine_amount is required for FINE payments")

        if not borrowing.actual_return_date:
            raise ValueError(
                "actual_return_date is required for FINE payments"
            )

        total_price = fine_amount
        days_overdue = (
            borrowing.actual_return_date - borrowing.expected_return_date
        ).days
        description = f"Fine for {days_overdue} days overdue"
        product_name = f"Overdue Fine: {borrowing.book.title}"

    else:
        raise ValueError(f"Unsupported payment_type: {payment_type}")

    amount_in_cents = int(total_price * 100)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": product_name,
                            "description": description,
                        },
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=request.build_absolute_uri(reverse("payments:success"))
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse("payments:cancel")),
        )

        return {
            "session_id": session.id,
            "session_url": session.url,
            "amount": total_price,
        }

    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")
