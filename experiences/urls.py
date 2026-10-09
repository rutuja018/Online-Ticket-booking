from django.urls import path
from . import views

app_name = 'experiences'

urlpatterns = [
    path('', views.experience_hub, name='hub'),
    path('submit/', views.submit_review, name='submit_review'),
    path('api/vote/<int:review_id>/', views.api_vote_helpful, name='api_vote_helpful'),
]
