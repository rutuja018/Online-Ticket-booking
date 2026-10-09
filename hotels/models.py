import random
import string
from decimal import Decimal
from datetime import time, date, datetime
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

from bookings.models import PromoCode


def generate_hotel_booking_ref():
    """Generates a unique Hotel Reference ID format like HTL-2026-8K92XP"""
    prefix = f"HTL-{timezone.now().year}-"
    while True:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        ref = f"{prefix}{suffix}"
        if not HotelBooking.objects.filter(booking_reference=ref).exists():
            return ref


class HotelAmenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon_class = models.CharField(max_length=100, default='fa-solid fa-check', help_text="FontAwesome icon e.g. fa-solid fa-wifi")
    description = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=True, help_text="Show in quick highlights")

    class Meta:
        ordering = ['name']
        verbose_name = "Hotel Amenity"
        verbose_name_plural = "Hotel Amenities"

    def __str__(self):
        return self.name


class Hotel(models.Model):
    HOTEL_TYPE_CHOICES = (
        ('LUXURY', 'Luxury Hotel & 5-Star Resort'),
        ('HERITAGE', 'Heritage Palace & Royal Haveli'),
        ('BUSINESS', 'Premium Business Hotel'),
        ('BOUTIQUE', 'Boutique & Lifestyle Stay'),
        ('RESORT', 'Beach & Nature Resort'),
        ('BUDGET', 'Comfort & Budget Stay'),
    )

    STAR_RATING_CHOICES = (
        (1, '1 Star ★'),
        (2, '2 Star ★★'),
        (3, '3 Star ★★★'),
        (4, '4 Star ★★★★'),
        (5, '5 Star ★★★★★'),
    )

    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    tagline = models.CharField(max_length=250, blank=True, default='')
    hotel_type = models.CharField(max_length=30, choices=HOTEL_TYPE_CHOICES, default='LUXURY')
    star_rating = models.PositiveSmallIntegerField(choices=STAR_RATING_CHOICES, default=4, db_index=True)
    guest_rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.5'), db_index=True)
    review_count = models.PositiveIntegerField(default=85)
    
    # Location
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    address = models.TextField()
    pincode = models.CharField(max_length=10, blank=True)
    landmark = models.CharField(max_length=200, blank=True, help_text="e.g. Near New Delhi Railway Station / 2km from Airport")
    
    # Description & Media
    description = models.TextField()
    main_image = models.CharField(max_length=500, help_text="URL or static asset image path")
    
    # Policies
    check_in_time = models.TimeField(default=time(14, 0))
    check_out_time = models.TimeField(default=time(11, 0))
    cancellation_policy = models.TextField(
        default="Free cancellation up to 24 hours before check-in date. Cancellations within 24 hours incur a 1-night room charge."
    )
    house_rules = models.TextField(
        blank=True,
        default="Government-issued Photo ID required for all adult guests at check-in (Aadhaar, Passport, DL). Couples welcome with valid ID proof."
    )
    
    # Amenities & Attributes
    amenities = models.ManyToManyField(HotelAmenity, related_name='hotels', blank=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-guest_rating', 'name']
        verbose_name = "Hotel"
        verbose_name_plural = "Hotels"

    def __str__(self):
        return f"{self.name} ({self.city}) - {self.star_rating}★"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.city}")
            candidate = base_slug
            idx = 1
            while Hotel.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{idx}"
                idx += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def min_price(self):
        """Returns the minimum price per night among active rooms"""
        active_rooms = self.rooms.filter(is_active=True, available_rooms__gt=0)
        if active_rooms.exists():
            min_room = active_rooms.order_by('price_per_night').first()
            return min_room.price_per_night
        # Fallback to any active room
        any_room = self.rooms.filter(is_active=True).order_by('price_per_night').first()
        return any_room.price_per_night if any_room else Decimal('1999.00')

    @property
    def star_range(self):
        return range(self.star_rating)

    @property
    def empty_star_range(self):
        return range(5 - self.star_rating)

    @property
    def rating_badge_class(self):
        if self.guest_rating >= Decimal('4.5'):
            return 'badge-success'
        elif self.guest_rating >= Decimal('4.0'):
            return 'badge-primary'
        elif self.guest_rating >= Decimal('3.5'):
            return 'badge-warning'
        return 'badge-neutral'

    @property
    def rating_text(self):
        if self.guest_rating >= Decimal('4.7'):
            return 'Exceptional'
        elif self.guest_rating >= Decimal('4.3'):
            return 'Excellent'
        elif self.guest_rating >= Decimal('4.0'):
            return 'Very Good'
        elif self.guest_rating >= Decimal('3.5'):
            return 'Good'
        return 'Pleasant'


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='gallery_images')
    image_url = models.CharField(max_length=500)
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'id']
        verbose_name = "Hotel Gallery Image"
        verbose_name_plural = "Hotel Gallery Images"

    def __str__(self):
        return f"{self.hotel.name} - Image {self.id}"


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=100, help_text="e.g. Deluxe Room, Executive Suite, Luxury Royal Suite")
    description = models.TextField(blank=True)
    bed_type = models.CharField(max_length=100, default='1 King Bed or 2 Twin Beds')
    room_size_sqft = models.PositiveIntegerField(default=320, help_text="Room area in sq. ft.")
    max_adults = models.PositiveIntegerField(default=2)
    max_children = models.PositiveIntegerField(default=1)
    max_occupancy = models.PositiveIntegerField(default=3)
    
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base rate per night (₹)")
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Optional discounted promo rate")
    
    total_rooms = models.PositiveIntegerField(default=10)
    available_rooms = models.PositiveIntegerField(default=10)
    
    image_url = models.CharField(max_length=500, blank=True, help_text="Room photo URL or static path")
    
    # Inclusions & In-room amenities
    has_free_breakfast = models.BooleanField(default=True)
    has_free_cancellation = models.BooleanField(default=True)
    has_ac = models.BooleanField(default=True)
    has_wifi = models.BooleanField(default=True)
    has_city_view = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    custom_facilities = models.CharField(
        max_length=300,
        blank=True,
        default="LED Smart TV, Mini Refrigerator, Tea/Coffee Maker, Electronic Safe, Rain Shower",
        help_text="Comma-separated amenities"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_per_night']
        verbose_name = "Room Category"
        verbose_name_plural = "Room Categories"

    def __str__(self):
        return f"{self.hotel.name} - {self.room_type} (₹{self.price_per_night}/night)"

    @property
    def facilities_list(self):
        if not self.custom_facilities:
            return []
        return [f.strip() for f in self.custom_facilities.split(',') if f.strip()]

    @property
    def effective_price(self):
        return self.discounted_price if self.discounted_price and self.discounted_price < self.price_per_night else self.price_per_night


class HotelBooking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed / Checked Out'),
        ('REFUNDED', 'Refund Processed'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('SUCCESS', 'Payment Successful'),
        ('FAILED', 'Payment Failed'),
        ('REFUNDED', 'Refund Processed'),
    )

    booking_reference = models.CharField(
        max_length=30, unique=True, default=generate_hotel_booking_ref, db_index=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_bookings')
    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings')
    
    # Stay Specs
    room_count = models.PositiveIntegerField(default=1)
    guest_count = models.PositiveIntegerField(default=2)
    check_in_date = models.DateField(db_index=True)
    check_out_date = models.DateField(db_index=True)
    nights = models.PositiveIntegerField(default=1)
    
    # Primary Guest Information
    primary_guest_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    special_requests = models.TextField(blank=True, null=True, help_text="e.g. Non-smoking room, high floor, early check-in")
    
    # Fare Breakdown
    base_price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, help_text="nights * rooms * price_per_night")
    taxes = models.DecimalField(max_digits=10, decimal_places=2, help_text="Hotel GST (12%)")
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('49.00'), help_text="Platform Convenience Fee")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Promo Code
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    promo_code_obj = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='hotel_bookings'
    )
    
    # Status
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # Cancellation & Refund
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Hotel Reservation"
        verbose_name_plural = "Hotel Reservations"

    def __str__(self):
        return f"{self.booking_reference} - {self.hotel.name} - {self.primary_guest_name} ({self.booking_status})"

    @property
    def is_upcoming(self):
        return self.check_in_date >= timezone.now().date() and self.booking_status == 'CONFIRMED'

    @property
    def is_confirmed(self):
        return self.booking_status == 'CONFIRMED'

    @property
    def is_cancelled(self):
        return self.booking_status in ['CANCELLED', 'REFUNDED']

    @property
    def is_cancellable(self):
        can_cancel, _ = self.can_be_cancelled()
        return can_cancel

    def can_be_cancelled(self):
        """
        Hotel cancellation policy:
        - Must be PENDING or CONFIRMED
        - Can be cancelled anytime before check-in date
        """
        if self.booking_status == 'PENDING':
            return True, "Pending reservation can be cancelled."

        if self.booking_status != 'CONFIRMED':
            return False, f"Booking with status '{self.booking_status}' cannot be cancelled."

        today = timezone.now().date()
        if self.check_in_date < today:
            return False, "Cannot cancel past or ongoing hotel bookings."

        return True, "Eligible for cancellation."

    def calculate_refund(self):
        """
        Refund Calculation Policy:
        - If PENDING: 0 refund
        - If cancelled >= 2 days prior to check-in: 100% of base fare + 100% taxes (service fee retained)
        - If cancelled 1 day prior: 80% of base fare + taxes
        - If cancelled on check-in day: 50% of base fare
        """
        if self.booking_status == 'PENDING' or self.payment_status != 'SUCCESS':
            return Decimal('0.00')

        today = timezone.now().date()
        days_ahead = (self.check_in_date - today).days

        if days_ahead >= 2:
            refund = self.base_fare + self.taxes
        elif days_ahead == 1:
            refund = (self.base_fare * Decimal('0.80')) + self.taxes
        else:
            refund = self.base_fare * Decimal('0.50')

        return max(Decimal('0.00'), round(refund, 2))

    @transaction.atomic
    def cancel_and_release_rooms(self, reason="Customer requested cancellation"):
        """
        Safely cancels hotel reservation and releases room inventory.
        """
        can_cancel, msg = self.can_be_cancelled()
        if not can_cancel:
            return False, msg

        # Release rooms back to inventory
        if self.room:
            Room.objects.filter(id=self.room_id).update(
                available_rooms=models.F('available_rooms') + self.room_count
            )

        refund = self.calculate_refund()
        self.booking_status = 'CANCELLED'
        self.payment_status = 'REFUNDED' if refund > 0 else 'CANCELLED'
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.refund_amount = refund
        self.save()

        if refund > 0:
            return True, f"Hotel Booking {self.booking_reference} has been cancelled. Refund of ₹{refund} initiated."
        return True, f"Hotel Booking {self.booking_reference} has been cancelled."


class HotelGuest(models.Model):
    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    )

    booking = models.ForeignKey(HotelBooking, on_delete=models.CASCADE, related_name='guests')
    full_name = models.CharField(max_length=120)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='MALE')
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        verbose_name = "Hotel Guest"
        verbose_name_plural = "Hotel Guests"

    def __str__(self):
        return f"{self.full_name} ({self.booking.booking_reference})"


class HotelReview(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=150)
    comment = models.TextField()
    stay_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Hotel Review"
        verbose_name_plural = "Hotel Reviews"

    def __str__(self):
        return f"{self.hotel.name} - {self.rating}★ by {self.user.username}"
