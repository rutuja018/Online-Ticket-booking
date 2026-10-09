from django.contrib import admin
from .models import StationRetiringRoom, RetiringRoomBooking

@admin.register(StationRetiringRoom)
class StationRetiringRoomAdmin(admin.ModelAdmin):
    list_display = ('station', 'room_type', 'room_or_bed_no', 'price_12h', 'price_24h', 'capacity', 'is_active')
    list_filter = ('room_type', 'is_active', 'station__city')
    search_fields = ('station__name', 'station__code', 'room_or_bed_no')

@admin.register(RetiringRoomBooking)
class RetiringRoomBookingAdmin(admin.ModelAdmin):
    list_display = ('booking_ref', 'guest_name', 'station', 'room', 'slot_type', 'check_in_date', 'total_amount', 'booking_status', 'created_at')
    list_filter = ('booking_status', 'slot_type', 'station')
    search_fields = ('booking_ref', 'guest_name', 'guest_phone', 'train_pnr', 'guest_id_number')
