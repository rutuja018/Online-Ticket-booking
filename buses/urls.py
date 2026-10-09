from django.urls import path
from . import views

app_name = 'buses'

urlpatterns = [
    path('', views.search_buses, name='search'),
    path('schedule/<int:schedule_id>/', views.bus_detail, name='detail'),
    path('schedule/<int:schedule_id>/seats/', views.bus_seat_select, name='seat_select'),
    path('api/fare-calendar/', views.bus_fare_calendar_api, name='fare_calendar_api'),
]
