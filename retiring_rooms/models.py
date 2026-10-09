import random
import string
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from railways.models import RailwayStation

def generate_retiring_room_ref():
    """Generates unique booking reference e.g. RR-NDLS-8A91F2"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"RR-{suffix}"

class StationRetiringRoom(models.Model):
    ROOM_TYPE_CHOICES = (
        ('AC_DORMITORY', 'AC Dormitory Bed'),
        ('NON_AC_STANDARD', 'Non-AC Standard Room'),
        ('AC_DELUXE', 'AC Deluxe Double Room'),
        ('EXECUTIVE_SUITE', 'Executive Station Suite'),
    )

    station = models.ForeignKey(RailwayStation, on_delete=models.CASCADE, related_name='retiring_rooms')
    room_type = models.CharField(max_length=30, choices=ROOM_TYPE_CHOICES, default='AC_DELUXE', db_index=True)
    room_or_bed_no = models.CharField(max_length=30, help_text="e.g. Bed D-04 or Room 208")
    floor = models.CharField(max_length=100, default='Platform 1, 1st Floor Concourse')
    
    price_12h = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('500.00'), help_text="Rate for 12 hours slot")
    price_24h = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('900.00'), help_text="Rate for 24 hours full day")
    price_48h = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1650.00'), help_text="Rate for 48 hours")
    
    capacity = models.PositiveIntegerField(default=2)
    amenities = models.CharField(max_length=300, default='Free High-Speed WiFi, Air Conditioning, Hot Water Shower, Clean Linen, Personal Locker, Charging Station')
    image_url = models.CharField(max_length=500, default='https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['station', 'room_type', 'price_12h']
        verbose_name = "Station Retiring Room / Bed"
        verbose_name_plural = "Station Retiring Rooms & Beds"

    def __str__(self):
        return f"{self.station.code} - {self.get_room_type_display()} ({self.room_or_bed_no}) - ₹{self.price_12h}/12h"

    def get_price_for_slot(self, slot_type):
        if slot_type == '12_HOURS':
            return self.price_12h
        elif slot_type == '48_HOURS':
            return self.price_48h
        return self.price_24h


class RetiringRoomBooking(models.Model):
    SLOT_CHOICES = (
        ('12_HOURS', '12 Hours Slot'),
        ('24_HOURS', '24 Hours (Full Day)'),
        ('48_HOURS', '48 Hours (2 Days)'),
    )

    STATUS_CHOICES = (
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('SUCCESS', 'Payment Successful'),
        ('PENDING', 'Pending Payment'),
        ('REFUNDED', 'Refunded'),
    )

    GENDER_CHOICES = (
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    )

    ID_TYPE_CHOICES = (
        ('AADHAAR', 'Aadhaar Card'),
        ('PASSPORT', 'Passport'),
        ('DRIVING_LICENSE', 'Driving License'),
        ('VOTER_ID', 'Voter ID'),
    )

    booking_ref = models.CharField(max_length=30, unique=True, default=generate_retiring_room_ref, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='retiring_room_bookings')
    station = models.ForeignKey(RailwayStation, on_delete=models.CASCADE, related_name='room_reservations')
    room = models.ForeignKey(StationRetiringRoom, on_delete=models.CASCADE, related_name='reservations')
    
    slot_type = models.CharField(max_length=20, choices=SLOT_CHOICES, default='24_HOURS')
    check_in_date = models.DateField(db_index=True)
    check_in_time_slot = models.CharField(max_length=50, default='08:00 AM - 08:00 PM')
    check_out_date = models.DateField()
    
    guest_count = models.PositiveIntegerField(default=1)
    guest_name = models.CharField(max_length=120)
    guest_age = models.PositiveIntegerField(default=30)
    guest_gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='MALE')
    guest_phone = models.CharField(max_length=20)
    guest_email = models.EmailField(blank=True, default='')
    guest_id_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, default='AADHAAR')
    guest_id_number = models.CharField(max_length=50)
    
    train_pnr = models.CharField(max_length=30, blank=True, default='', help_text="Associated Train PNR (optional)")
    
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED', db_index=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='SUCCESS')
    payment_method = models.CharField(max_length=30, default='UPI')
    
    cancellation_reason = models.TextField(blank=True, default='')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Retiring Room Booking"
        verbose_name_plural = "Retiring Room Bookings"

    def __str__(self):
        return f"{self.booking_ref} - {self.guest_name} @ {self.station.code} ({self.room.get_room_type_display()})"

    @property
    def is_active(self):
        return self.booking_status in ['CONFIRMED', 'CHECKED_IN'] and self.check_in_date >= timezone.now().date()
