from django.contrib.auth import get_user_model
from django.db import models

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="borrowings",
    )

    def __str__(self):
        return (
            f"From: {self.borrow_date} "
            f"till: {self.expected_return_date} "
            f"returned: {self.actual_return_date}"
        )

    @staticmethod
    def validate_expected_return_date(
        expected_return_date, borrow_date, error_to_raise
    ):
        if expected_return_date < borrow_date:
            raise error_to_raise(
                "Expected return date cannot be before borrow date."
            )

    @staticmethod
    def validate_actual_return_date(
        actual_return_date, borrow_date, error_to_raise
    ):
        if actual_return_date < borrow_date:
            raise error_to_raise(
                "Actual return date cannot be before borrow date"
            )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    expected_return_date__gte=models.F("borrow_date")
                ),
                name="expected_after_borrow",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(actual_return_date__isnull=True)
                    | models.Q(actual_return_date__gte=models.F("borrow_date"))
                ),
                name="actual_after_borrow",
            ),
            models.UniqueConstraint(
                fields=["book", "user"],
                condition=models.Q(actual_return_date__isnull=True),
                name="unique_active_borrowing",
            ),
        ]
