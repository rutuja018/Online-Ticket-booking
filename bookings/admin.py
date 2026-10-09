from django.contrib import admin
from .models import Booking, Passenger, PromoCode

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'title', 'discount_type', 'discount_amount', 'applicable_transport',
        'min_booking_amount', 'valid_from', 'valid_to', 'usage_limit', 'used_count', 'is_active'
    )
    list_filter = ('is_active', 'applicable_transport', 'discount_type', 'valid_from', 'valid_to')
    search_fields = ('code', 'title', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('used_count', 'created_at', 'updated_at')

class PassengerInline(admin.TabularInline):
    model = Passenger
    extra = 0
    fields = ('full_name', 'age', 'gender', 'seat_number', 'id_type', 'id_number')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'pnr', 'user', 'transport_type', 'service_title', 'journey_date',
        'passenger_count', 'discount', 'total_amount', 'promo_code',
        'booking_status', 'payment_status', 'created_at'
    )
    list_filter = ('transport_type', 'booking_status', 'payment_status', 'journey_date')
    search_fields = ('pnr', 'user__username', 'user__email', 'service_title', 'source_location', 'destination_location', 'promo_code')
    readonly_fields = ('pnr', 'created_at', 'updated_at')
    inlines = [PassengerInline]

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'booking', 'seat_number', 'age', 'gender', 'id_type', 'id_number')
    search_fields = ('full_name', 'booking__pnr', 'id_number')

