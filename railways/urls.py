from django.urls import path
from . import views

app_name = 'railways'

urlpatterns = [
    path('', views.search_trains, name='search'),
    path('schedule/<int:schedule_id>/', views.train_detail, name='detail'),
    path('schedule/<int:schedule_id>/seats/', views.train_seat_select, name='seat_select'),
    path('api/fare-calendar/', views.train_fare_calendar_api, name='fare_calendar_api'),
]
