from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('<int:booking_id>/', views.process_payment, name='process_payment'),
]
