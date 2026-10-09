from django.urls import path
from . import views

app_name = 'hotels'

urlpatterns = [
    path('', views.hotel_list, name='index'),
    path('search/', views.hotel_list, name='search'),
    path('<int:hotel_id>/', views.hotel_detail, name='detail'),
    path('<int:hotel_id>/book/<int:room_id>/', views.book_room, name='book_room'),
    path('payment/<int:booking_id>/', views.hotel_process_payment, name='process_payment'),
    path('confirmation/<str:booking_ref>/', views.hotel_booking_confirmation, name='confirmation'),
    path('cancel/<str:booking_ref>/', views.hotel_booking_cancel, name='cancel'),
    
    # AJAX APIs
    path('api/validate-promo/', views.hotel_validate_promo, name='validate_promo'),
    path('api/calculate-price/', views.hotel_calculate_price, name='calculate_price'),
]
