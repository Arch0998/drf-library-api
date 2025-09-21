from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=256)
    author = models.CharField(max_length=128)
    cover = models.CharField(
        max_length=16,
        choices=[
            ("HARD", "Hardcover"),
            ("SOFT", "Softcover"),
        ],
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.title} by {self.author}"

    class Meta:
        ordering = ["title", "author"]
        verbose_name = "Book"
        verbose_name_plural = "Books"
