from django.urls import path
from . import views

app_name = 'retiring_rooms'

urlpatterns = [
    path('', views.retiring_room_index, name='index'),
    path('search/', views.retiring_room_index, name='search'),
    path('room/<int:room_id>/', views.room_detail, name='detail'),
    path('book/<int:room_id>/', views.book_room, name='book'),
    path('process-payment/<int:room_id>/', views.process_room_payment, name='process_payment'),
    path('pass/<str:booking_ref>/', views.booking_pass, name='booking_pass'),
    path('cancel/<str:booking_ref>/', views.cancel_booking, name='cancel'),
]
