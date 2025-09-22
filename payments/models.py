from django.db import models
from django.db.models import Q # noqa


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "PENDING"
    PAID = "PAID", "PAID"


class PaymentType(models.TextChoices):
    PAYMENT = "PAYMENT", "PAYMENT"
    FINE = "FINE", "FINE"


class Payment(models.Model):
    """Payment model. Used to store payments.
    The status of the payment is stored in the status field.
    The type of the payment is stored in the type field."""

    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    payment_type = models.CharField(
        max_length=10,
        choices=PaymentType.choices,
        default=PaymentType.PAYMENT,
        db_index=True,
    )

    """Implemented as ForeignKey to Borrowing model. After Borrowing model implementation,
    this field will be used to store the borrowing that is being paid for."""
    # borrowing = models.ForeignKey(
    #     "borrowings.Borrowing",
    #     on_delete=models.PROTECT,
    #     related_name="payments",
    #     db_index=True,
    # )
    """Temporary field to store borrowing id. Before Borrowing model implementation use this field
    to store the borrowing that is being paid for."""
    borrowing_id = models.PositiveIntegerField(db_index=True)

    session_url = models.URLField(max_length=512, blank=True, null=True)
    session_id = models.CharField(
        max_length=255, blank=True, null=True, db_index=True
    )

    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    """Constraints and indexes. Can be used only after Borrowing model implementation."""
    class Meta:
        db_table = "payment"
        constraints = [
            models.CheckConstraint(
                check=Q(money_to_pay__gte=0),
                name="money_to_pay_non_negative",
            ),
            models.UniqueConstraint(
                fields=["borrowing_id", "payment_type"],
                condition=Q(status=PaymentStatus.PENDING),
                name="uniq_pending_payment_per_borrowing_type_tmp",
            ),
        ]

    def __str__(self):
        return f"""Payment(id={self.pk}, status={self.status},
        type={self.payment_type}, borrowing_id={self.borrowing_id},
        amount={self.money_to_pay} USD)"""
