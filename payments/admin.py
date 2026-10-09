from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'get_pnr', 'get_user', 'amount', 'payment_method',
        'payment_status', 'created_at'
    )
    list_filter = ('payment_method', 'payment_status', 'created_at')
    search_fields = ('transaction_id', 'booking__pnr', 'booking__user__username', 'card_last4', 'upi_id')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')

    def get_pnr(self, obj):
        return obj.booking.pnr
    get_pnr.short_description = 'Booking PNR'

    def get_user(self, obj):
        return obj.booking.user.username
    get_user.short_description = 'Customer'
