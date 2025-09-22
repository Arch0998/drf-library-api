from django.contrib import admin
from payments.models import Payment

"""
Use this to register Payment model in admin panel
after Borrowing model implementation
"""
# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = (
#     "id", "status", "payment_type", "borrowing", "money_to_pay", "session_id"
#     )
#     list_filter = ("status", "payment_type")
#     search_fields = ("session_id", "borrowing__id")
#     readonly_fields = ("session_url", "session_id")
#     ordering = ("-id",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "payment_type",
        "money_to_pay",
        "session_id",
    )
    list_filter = ("status", "payment_type")
    search_fields = ("session_id",)
    readonly_fields = ("session_url", "session_id")
    ordering = ("-id",)
