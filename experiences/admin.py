from django.contrib import admin
from .models import CustomerReview, ReviewHelpfulVote

@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer_name', 'booking_type', 'rating', 'title', 'verified_traveler', 'is_featured', 'helpful_votes', 'created_at')
    list_filter = ('booking_type', 'rating', 'verified_traveler', 'is_featured')
    search_fields = ('reviewer_name', 'title', 'review_text', 'pnr_or_ref', 'service_name')
    list_editable = ('is_featured', 'verified_traveler')

@admin.register(ReviewHelpfulVote)
class ReviewHelpfulVoteAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'session_key', 'created_at')
