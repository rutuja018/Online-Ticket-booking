import random
import string
from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, time

from railways.models import TrainSchedule, TrainSeat
from airlines.models import FlightSchedule, FlightSeat
from buses.models import BusSchedule, BusSeat


def generate_unique_pnr():
    """Generates a unique PNR format like RAW-2026-8F73K2"""
    prefix = f"RAW-{timezone.now().year}-"
    while True:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        pnr = f"{prefix}{suffix}"
        if not Booking.objects.filter(pnr=pnr).exists():
            return pnr


class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('FIXED', 'Fixed Amount (₹)'),
        ('PERCENT', 'Percentage (%)'),
    )

    TRANSPORT_SCOPE_CHOICES = (
        ('ALL', 'All Transports'),
        ('FLIGHT', 'Flights Only'),
        ('TRAIN', 'Trains Only'),
        ('BUS', 'Buses Only'),
    )

    code = models.CharField(max_length=50, unique=True, db_index=True, help_text="Uppercase promo code e.g. TRAVELNOW")
    title = models.CharField(max_length=150, blank=True, default='', help_text="e.g. Flight Special Discount")
    description = models.TextField(blank=True, help_text="Details regarding offer eligibility")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='FIXED')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('100.00'), help_text="Discount value in ₹ or %")
    min_booking_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Minimum total booking fare required")
    max_discount_cap = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum discount cap for percentage promos")
    applicable_transport = models.CharField(max_length=20, choices=TRANSPORT_SCOPE_CHOICES, default='ALL')
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField(null=True, blank=True, help_text="Leave blank for no expiration")
    usage_limit = models.PositiveIntegerField(default=1000, help_text="Max times this promo code can be used in total")
    used_count = models.PositiveIntegerField(default=0, help_text="Times this promo code has been redeemed")
    per_user_limit = models.PositiveIntegerField(default=1, help_text="Max usages per single customer account")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"

    def __str__(self):
        type_str = f"₹{self.discount_amount}" if self.discount_type == 'FIXED' else f"{self.discount_amount}%"
        return f"{self.code} ({type_str} off - {self.get_applicable_transport_display()})"

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid_for_booking(self, booking_amount, transport_type, user=None):
        """
        Validates promo code for a given booking.
        Returns (is_valid: bool, discount_amount: Decimal, message: str)
        """
        if not self.is_active:
            return False, Decimal('0.00'), f"Promo code '{self.code}' is currently inactive."

        today = timezone.now().date()
        if self.valid_from and today < self.valid_from:
            return False, Decimal('0.00'), f"Promo code '{self.code}' is not active yet (starts {self.valid_from.strftime('%d %b %Y')})."

        if self.valid_to and today > self.valid_to:
            return False, Decimal('0.00'), f"Promo code '{self.code}' has expired on {self.valid_to.strftime('%d %b %Y')}."

        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, Decimal('0.00'), f"Promo code '{self.code}' usage limit has been reached."

        if self.applicable_transport != 'ALL' and self.applicable_transport != transport_type:
            transport_name = dict(self.TRANSPORT_SCOPE_CHOICES).get(self.applicable_transport, self.applicable_transport)
            return False, Decimal('0.00'), f"Promo code '{self.code}' is only valid for {transport_name} bookings."

        if booking_amount < self.min_booking_amount:
            return False, Decimal('0.00'), f"Minimum booking amount of ₹{self.min_booking_amount} is required for promo '{self.code}'."

        if user and user.is_authenticated and self.per_user_limit:
            user_used = Booking.objects.filter(
                user=user,
                promo_code_obj=self,
                booking_status__in=['CONFIRMED', 'PENDING']
            ).count()
            if user_used >= self.per_user_limit:
                return False, Decimal('0.00'), f"You have already used promo code '{self.code}' the maximum allowed times ({self.per_user_limit})."

        calculated_discount = self.calculate_discount(booking_amount)
        return True, calculated_discount, f"Promo code '{self.code}' applied! You saved ₹{calculated_discount}."

    def calculate_discount(self, booking_amount):
        """Calculates discount based on fixed or percentage type."""
        if self.discount_type == 'PERCENT':
            discount = (booking_amount * (self.discount_amount / Decimal('100.00')))
            if self.max_discount_cap:
                discount = min(discount, self.max_discount_cap)
        else:
            discount = self.discount_amount

        discount = min(discount, booking_amount)
        return max(Decimal('0.00'), round(discount, 2))


class Booking(models.Model):
    TRANSPORT_CHOICES = (
        ('TRAIN', 'Train / Railway'),
        ('FLIGHT', 'Flight / Airline'),
        ('BUS', 'Bus Travel'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('REFUNDED', 'Refunded'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending Payment'),
        ('SUCCESS', 'Payment Successful'),
        ('FAILED', 'Payment Failed'),
        ('REFUNDED', 'Refund Processed'),
    )

    pnr = models.CharField(max_length=30, unique=True, default=generate_unique_pnr, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES)
    
    # Specific Schedule Relationships
    train_schedule = models.ForeignKey(
        TrainSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='train_bookings'
    )
    flight_schedule = models.ForeignKey(
        FlightSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='flight_bookings'
    )
    bus_schedule = models.ForeignKey(
        BusSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='bus_bookings'
    )

    # Journey Details Snapshot
    service_title = models.CharField(max_length=200, help_text="e.g. Vande Bharat Express 22436 / AI-805 / IntrCity SmartBus")
    travel_class = models.CharField(max_length=50)
    source_location = models.CharField(max_length=150)
    destination_location = models.CharField(max_length=150)
    journey_date = models.DateField(db_index=True)
    departure_time = models.CharField(max_length=50)
    arrival_time = models.CharField(max_length=50)
    duration_text = models.CharField(max_length=50, blank=True)
    
    # Passengers and Seats
    passenger_count = models.PositiveIntegerField(default=1)
    allocated_seats = models.CharField(max_length=200, help_text="Comma-separated seat numbers e.g. B1-12, B1-13")

    # Fare Breakdown (all Decimals)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="GST / Airport Tax")
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'), help_text="Platform Convenience Fee")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Promo Code Tracking
    promo_code = models.CharField(max_length=50, blank=True, null=True, help_text="Applied promo code string")
    promo_code_obj = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings'
    )

    # Status
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    # Cancellation Metadata
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"{self.pnr} ({self.get_transport_type_display()}) - {self.user.username} - {self.booking_status}"

    @property
    def is_upcoming(self):
        return self.journey_date >= timezone.now().date() and self.booking_status == 'CONFIRMED'

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
        Cancellation rules:
        - Must be CONFIRMED or PENDING
        - If CONFIRMED, must be at least 4 hours before scheduled departure date/time
        """
        if self.booking_status == 'PENDING':
            return True, "Pending reservation can be cancelled."

        if self.booking_status != 'CONFIRMED':
            return False, f"Booking with status '{self.booking_status}' cannot be cancelled."

        today = timezone.now().date()
        if self.journey_date < today:
            return False, "Cannot cancel past journey bookings."

        # If journey is today, verify departure time
        if self.journey_date == today:
            try:
                # Try parsing departure time format HH:MM
                dep_time_str = self.departure_time.strip()
                if ":" in dep_time_str:
                    parts = dep_time_str.split(":")
                    hour = int(parts[0])
                    minute = int(parts[1][:2])
                    dep_dt = datetime.combine(self.journey_date, time(hour, minute))
                    dep_dt = timezone.make_aware(dep_dt, timezone.get_current_timezone())
                    
                    # 4 hours cutoff
                    diff = dep_dt - timezone.now()
                    if diff.total_seconds() < 4 * 3600:
                        return False, "Cancellations are allowed only up to 4 hours before departure."
            except Exception:
                pass

        return True, "Eligible for cancellation."

    def calculate_refund(self):
        """
        Refund Calculation Policy:
        - If PENDING: 0 refund
        - If cancelled > 24 hours prior: 90% of base fare + taxes
        - If cancelled 4 - 24 hours prior: 75% of base fare + 50% taxes
        - If cancelled same day (> 4h prior): 50% of base fare
        - Convenience fee non-refundable
        """
        if self.booking_status == 'PENDING' or self.payment_status != 'SUCCESS':
            return Decimal('0.00')

        refundable_base = self.base_fare
        today = timezone.now().date()
        days_ahead = (self.journey_date - today).days

        if days_ahead >= 2:
            refund = (refundable_base * Decimal('0.90')) + self.taxes
        elif days_ahead == 1:
            refund = (refundable_base * Decimal('0.75')) + (self.taxes * Decimal('0.50'))
        else:
            refund = refundable_base * Decimal('0.50')

        return max(Decimal('0.00'), round(refund, 2))

    @transaction.atomic
    def cancel_and_release_seats(self, reason="Customer requested cancellation"):
        """
        Safely cancels booking and releases seats back into availability inventory.
        """
        can_cancel, msg = self.can_be_cancelled()
        if not can_cancel:
            return False, msg

        seat_list = [s.strip() for s in self.allocated_seats.split(',') if s.strip()]

        # 1. Release train seats
        if self.transport_type == 'TRAIN' and self.train_schedule:
            for s_str in seat_list:
                coach_seat = s_str.split('-')
                if len(coach_seat) == 2:
                    TrainSeat.objects.filter(
                        schedule=self.train_schedule,
                        coach=coach_seat[0].strip(),
                        seat_number=coach_seat[1].strip()
                    ).update(is_booked=False)
                else:
                    TrainSeat.objects.filter(
                        schedule=self.train_schedule,
                        seat_number=s_str
                    ).update(is_booked=False)

        # 2. Release flight seats
        elif self.transport_type == 'FLIGHT' and self.flight_schedule:
            for s_str in seat_list:
                FlightSeat.objects.filter(
                    schedule=self.flight_schedule,
                    seat_number=s_str
                ).update(is_booked=False)

        # 3. Release bus seats
        elif self.transport_type == 'BUS' and self.bus_schedule:
            for s_str in seat_list:
                BusSeat.objects.filter(
                    schedule=self.bus_schedule,
                    seat_number=s_str
                ).update(is_booked=False)

        # Calculate refund and update booking
        refund = self.calculate_refund()
        self.booking_status = 'CANCELLED'
        self.payment_status = 'REFUNDED' if refund > 0 else 'CANCELLED'
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.refund_amount = refund
        self.save()

        # Update payment record if exists
        if hasattr(self, 'payment') and self.payment:
            self.payment.payment_status = 'REFUNDED' if refund > 0 else 'FAILED'
            self.payment.save()

        if refund > 0:
            return True, f"Booking {self.pnr} has been successfully cancelled. Refund of ₹{refund} initiated."
        return True, f"Booking {self.pnr} has been successfully cancelled."


class Passenger(models.Model):
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
        ('PAN_CARD', 'PAN Card'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    full_name = models.CharField(max_length=120)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    id_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, default='AADHAAR')
    id_number = models.CharField(max_length=50)
    seat_number = models.CharField(max_length=20)
    berth_preference = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = "Passenger"
        verbose_name_plural = "Passengers"

    def __str__(self):
        return f"{self.full_name} ({self.seat_number}) - PNR: {self.booking.pnr}"

    @property
    def masked_id(self):
        """Mask ID for security (e.g. XXXX-XXXX-1234)"""
        if not self.id_number or len(self.id_number) < 4:
            return "XXXX"
        return "X" * (len(self.id_number) - 4) + self.id_number[-4:]
