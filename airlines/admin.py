from django.contrib import admin
from .models import Airport, Airline, Aircraft, Flight, FlightSchedule, FlightSeat

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'city', 'country', 'terminal', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('code', 'name', 'city')

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'callsign')
    search_fields = ('code', 'name')

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'total_capacity')
    search_fields = ('model_name',)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_number', 'airline', 'aircraft', 'is_active')
    list_filter = ('airline', 'is_active')
    search_fields = ('flight_number', 'airline__name')

class FlightSeatInline(admin.TabularInline):
    model = FlightSeat
    extra = 0
    fields = ('seat_number', 'cabin_class', 'seat_type', 'is_booked')

@admin.register(FlightSchedule)
class FlightScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'flight', 'origin_airport', 'destination_airport', 'departure_datetime',
        'arrival_datetime', 'duration_minutes', 'fare_economy', 'fare_business', 'is_active'
    )
    list_filter = ('origin_airport', 'destination_airport', 'is_active', 'stops')
    search_fields = ('flight__flight_number', 'origin_airport__city', 'destination_airport__city')
    inlines = [FlightSeatInline]

@admin.register(FlightSeat)
class FlightSeatAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'seat_number', 'cabin_class', 'seat_type', 'is_booked')
    list_filter = ('cabin_class', 'seat_type', 'is_booked')
    search_fields = ('seat_number', 'schedule__flight__flight_number')
