from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('create/', views.create_booking, name='create'),
    path('validate-promo/', views.validate_promo_code, name='validate_promo'),
    path('review/<int:booking_id>/', views.booking_review, name='review'),
    path('history/', views.booking_history, name='history'),
    path('calendar/', views.booking_calendar, name='calendar'),
    path('calendar/events/', views.booking_calendar_events_api, name='calendar_events_api'),
    path('calendar/export-ics/', views.export_calendar_ics, name='export_calendar_ics'),
    path('<str:pnr>/ticket/', views.booking_ticket, name='ticket'),
    path('<str:pnr>/cancel/', views.booking_cancel, name='cancel'),
]
