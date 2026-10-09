from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('send-otp/', views.send_email_otp_view, name='send_email_otp'),
    path('send-otp/', views.send_email_otp_view, name='send_otp'),
    path('verify-otp/', views.verify_email_otp_view, name='verify_email_otp'),
    path('verify-otp/', views.verify_email_otp_view, name='verify_otp'),
    path('guest-login/', views.guest_login_view, name='guest_login'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
]
