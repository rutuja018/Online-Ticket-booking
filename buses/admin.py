from django.contrib import admin
from .models import BusOperator, Bus, BusRoute, BusSchedule, BusSeat

@admin.register(BusOperator)
class BusOperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'rating', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('name',)

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_number', 'operator', 'bus_type', 'total_seats', 'is_ac', 'is_active')
    list_filter = ('bus_type', 'is_ac', 'is_active', 'operator')
    search_fields = ('bus_number', 'operator__name')

@admin.register(BusRoute)
class BusRouteAdmin(admin.ModelAdmin):
    list_display = ('source_city', 'destination_city', 'distance_km')
    search_fields = ('source_city', 'destination_city')

class BusSeatInline(admin.TabularInline):
    model = BusSeat
    extra = 0
    fields = ('seat_number', 'deck', 'seat_type', 'is_ladies_only', 'is_booked')

@admin.register(BusSchedule)
class BusScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'bus', 'route', 'journey_date', 'departure_time', 'arrival_time',
        'base_fare', 'is_active'
    )
    list_filter = ('journey_date', 'is_active', 'bus__bus_type')
    search_fields = ('bus__bus_number', 'route__source_city', 'route__destination_city')
    inlines = [BusSeatInline]

@admin.register(BusSeat)
class BusSeatAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'seat_number', 'deck', 'seat_type', 'is_ladies_only', 'is_booked')
    list_filter = ('deck', 'seat_type', 'is_ladies_only', 'is_booked')
    search_fields = ('seat_number', 'schedule__bus__bus_number')
