from django.urls import path
from . import views

app_name = 'food_catering'

urlpatterns = [
    path('', views.food_index, name='index'),
    path('menu/', views.restaurant_menu, name='menu'),
    path('menu/restaurant/<int:restaurant_id>/', views.restaurant_menu, name='restaurant_menu'),
    path('menu/station/<str:station_code>/', views.restaurant_menu, name='station_menu'),
    path('checkout/', views.food_checkout, name='checkout'),
    path('process-order/', views.food_process_order, name='process_order'),
    path('track/<str:order_ref>/', views.food_order_tracker, name='order_tracker'),
    path('cancel/<str:order_ref>/', views.cancel_food_order, name='cancel_order'),
    
    # AJAX APIs
    path('api/cart/update/', views.api_update_cart, name='api_update_cart'),
    path('api/pnr-lookup/', views.api_pnr_lookup, name='api_pnr_lookup'),
]
