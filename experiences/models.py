from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CustomerReview(models.Model):
    BOOKING_TYPE_CHOICES = (
        ('TRAIN', 'Train / Railway'),
        ('FLIGHT', 'Flight / Airline'),
        ('BUS', 'Bus Travel'),
        ('HOTEL', 'Hotel & Resort'),
        ('FOOD', 'Food in Train (E-Catering)'),
        ('RETIRING_ROOM', 'Station Retiring Room'),
        ('OVERALL', 'Overall Platform Experience'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    reviewer_name = models.CharField(max_length=120)
    reviewer_city = models.CharField(max_length=100, default='New Delhi')
    booking_type = models.CharField(max_length=30, choices=BOOKING_TYPE_CHOICES, default='OVERALL', db_index=True)
    pnr_or_ref = models.CharField(max_length=50, blank=True, null=True, help_text="Associated PNR or Booking Reference")
    service_name = models.CharField(max_length=150, blank=True, default='', help_text="e.g. Vande Bharat 22436 / Taj Hotel Goa")
    
    title = models.CharField(max_length=200)
    review_text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5, help_text="Overall rating between 1 and 5")
    
    # Sub-ratings (1-5)
    punctuality_rating = models.PositiveSmallIntegerField(default=5)
    cleanliness_rating = models.PositiveSmallIntegerField(default=5)
    service_rating = models.PositiveSmallIntegerField(default=5)
    value_rating = models.PositiveSmallIntegerField(default=5)
    
    verified_traveler = models.BooleanField(default=True)
    travel_tag = models.CharField(max_length=100, blank=True, default='Verified Traveler', help_text="e.g. Family Trip, Solo Traveler, Business")
    helpful_votes = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = "Customer Review"
        verbose_name_plural = "Customer Reviews"

    def __str__(self):
        return f"{self.reviewer_name} - {self.get_booking_type_display()} ({self.rating}★) - {self.title}"


class ReviewHelpfulVote(models.Model):
    review = models.ForeignKey(CustomerReview, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'session_key')
