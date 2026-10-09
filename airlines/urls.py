from django.urls import path
from . import views

app_name = 'airlines'

urlpatterns = [
    path('', views.search_flights, name='search'),
    path('schedule/<int:schedule_id>/', views.flight_detail, name='detail'),
    path('schedule/<int:schedule_id>/seats/', views.flight_seat_select, name='seat_select'),
    path('api/fare-calendar/', views.flight_fare_calendar_api, name='fare_calendar_api'),
]
