from django.contrib import admin
from .models import RailwayStation, Train, TrainSchedule, TrainSeat

@admin.register(RailwayStation)
class RailwayStationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'city', 'state', 'is_active')
    list_filter = ('is_active', 'state')
    search_fields = ('code', 'name', 'city')

class TrainSeatInline(admin.TabularInline):
    model = TrainSeat
    extra = 0
    fields = ('coach', 'seat_number', 'travel_class', 'berth_type', 'is_booked')
    readonly_fields = ()

@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ('train_number', 'name', 'train_type', 'total_coaches', 'is_active')
    list_filter = ('train_type', 'is_active')
    search_fields = ('train_number', 'name')

@admin.register(TrainSchedule)
class TrainScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'train', 'source_station', 'destination_station', 'journey_date',
        'departure_time', 'arrival_time', 'fare_sleeper', 'fare_ac3', 'is_active'
    )
    list_filter = ('journey_date', 'is_active', 'train__train_type')
    search_fields = ('train__train_number', 'train__name', 'source_station__name', 'destination_station__name')
    inlines = [TrainSeatInline]

@admin.register(TrainSeat)
class TrainSeatAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'coach', 'seat_number', 'travel_class', 'berth_type', 'is_booked')
    list_filter = ('travel_class', 'berth_type', 'is_booked', 'coach')
    search_fields = ('seat_number', 'schedule__train__train_number', 'coach')
