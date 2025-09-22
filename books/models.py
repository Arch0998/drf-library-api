from django.db import models
from django.core.validators import MinValueValidator


class Book(models.Model):
    title = models.CharField(
        max_length=256,
        help_text="The title of the book.",
    )
    author = models.CharField(
        max_length=128,
        help_text="The author of the book.",
    )
    cover = models.CharField(
        max_length=16,
        choices=[
            ("HARD", "Hardcover"),
            ("SOFT", "Softcover"),
        ],
        help_text="The cover type of the book (Hardcover or Softcover).",
    )
    inventory = models.PositiveIntegerField(
        help_text="The number of books available in inventory.",
    )
    daily_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="The daily fee for renting this book.",
    )

    def __str__(self):
        return f"{self.title} by {self.author}"

    class Meta:
        ordering = ["title", "author"]
        verbose_name = "Book"
        verbose_name_plural = "Books"
        unique_together = ("title", "author", "cover")
