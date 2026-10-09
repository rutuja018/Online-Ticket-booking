from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('price-finder/', views.price_finder, name='price_finder'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('terms/', views.terms, name='terms'),
    path('cancellation-refund-policy/', views.cancellation_policy, name='cancellation_policy'),
    path('cancellation-policy/', views.cancellation_policy, name='cancellation_policy_alias'),
]

