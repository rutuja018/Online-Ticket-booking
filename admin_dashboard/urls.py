from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_home, name='home'),
    path('trains/', views.manage_trains, name='manage_trains'),
    path('flights/', views.manage_flights, name='manage_flights'),
    path('buses/', views.manage_buses, name='manage_buses'),
    path('hotels/', views.manage_hotels, name='manage_hotels'),
    path('bookings/', views.manage_bookings, name='manage_bookings'),
    path('bookings/<int:booking_id>/cancel/', views.admin_cancel_booking, name='admin_cancel_booking'),
    path('users/', views.manage_users, name='manage_users'),
]
