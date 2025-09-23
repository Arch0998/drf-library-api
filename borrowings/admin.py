from django.contrib import admin

from borrowings.models import Borrowing


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "book",
        "borrow_date",
        "expected_return_date",
        "actual_return_date",
        "is_active",
    )

    list_filter = ("borrow_date", "expected_return_date", "actual_return_date")

    search_fields = (
        "user__email",
        "book__title",
        "book__author",
    )

    readonly_fields = ("borrow_date",)

    ordering = ("-borrow_date",)

    def is_active(self, obj):
        return obj.actual_return_date is None

    is_active.boolean = True
    is_active.short_description = "Active"
