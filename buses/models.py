from django.db import models
from decimal import Decimal

class BusOperator(models.Model):
    name = models.CharField(max_length=120, unique=True)
    contact_number = models.CharField(max_length=20, default="+91 1800-102-3344")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.5'))
    is_verified = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Bus Operator"
        verbose_name_plural = "Bus Operators"

    def __str__(self):
        return f"{self.name} (★ {self.rating})"


class Bus(models.Model):
    BUS_TYPE_CHOICES = (
        ('ORDINARY', 'Ordinary Express'),
        ('AC_SEATER', 'AC Seater (2+2)'),
        ('AC_SLEEPER', 'AC Sleeper (2+1)'),
        ('VOLVO', 'Volvo Multi-Axle Luxury AC'),
        ('SEMI_SLEEPER', 'Premium Semi-Sleeper AC'),
    )

    bus_number = models.CharField(max_length=30, unique=True, db_index=True)
    operator = models.ForeignKey(BusOperator, on_delete=models.CASCADE, related_name='buses')
    bus_type = models.CharField(max_length=30, choices=BUS_TYPE_CHOICES, default='VOLVO')
    total_seats = models.PositiveIntegerField(default=40)
    is_ac = models.BooleanField(default=True)
    has_sleeper = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['bus_number']
        verbose_name = "Bus"
        verbose_name_plural = "Buses"

    def __str__(self):
        return f"{self.operator.name} - {self.bus_number} ({self.get_bus_type_display()})"


class BusRoute(models.Model):
    source_city = models.CharField(max_length=100, db_index=True)
    destination_city = models.CharField(max_length=100, db_index=True)
    boarding_points = models.TextField(help_text="Comma separated boarding points")
    dropping_points = models.TextField(help_text="Comma separated dropping points")
    distance_km = models.PositiveIntegerField(default=350)

    class Meta:
        ordering = ['source_city', 'destination_city']
        verbose_name = "Bus Route"
        verbose_name_plural = "Bus Routes"

    def __str__(self):
        return f"{self.source_city} -> {self.destination_city} ({self.distance_km} km)"


class BusSchedule(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='schedules')
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name='schedules')
    journey_date = models.DateField(db_index=True)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(help_text="Journey duration in minutes")
    base_fare = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('850.00'))
    amenities = models.TextField(default="Air Conditioning, Free High-Speed WiFi, USB Charging Ports, Water Bottle, Clean Blankets, GPS Live Tracking")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['journey_date', 'departure_time']
        verbose_name = "Bus Schedule"
        verbose_name_plural = "Bus Schedules"

    def __str__(self):
        return f"{self.bus.operator.name} ({self.route.source_city} -> {self.route.destination_city}) on {self.journey_date}"

    @property
    def formatted_duration(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"

    def available_seat_count(self):
        if not self.seats.exists():
            self.generate_seats()
        return self.seats.filter(is_booked=False).count()

    def generate_seats(self):
        if self.seats.exists():
            return
        new_seats = []
        # Lower deck
        for s in range(1, 19):
            new_seats.append(BusSeat(
                schedule=self,
                seat_number=f"L{s}",
                deck='LOWER',
                seat_type='SEATER' if s <= 10 else 'SLEEPER',
                is_ladies_only=(s in [1, 2]),
                is_booked=(s in [3, 7])
            ))
        # Upper deck
        for s in range(1, 13):
            new_seats.append(BusSeat(
                schedule=self,
                seat_number=f"U{s}",
                deck='UPPER',
                seat_type='SLEEPER',
                is_ladies_only=False,
                is_booked=(s in [1, 5])
            ))
        BusSeat.objects.bulk_create(new_seats, ignore_conflicts=True)


class BusSeat(models.Model):
    DECK_CHOICES = (
        ('LOWER', 'Lower Deck'),
        ('UPPER', 'Upper Deck'),
    )

    SEAT_TYPE_CHOICES = (
        ('SEATER', 'Pushback Seater'),
        ('SLEEPER', 'Single / Double Sleeper Berth'),
    )

    schedule = models.ForeignKey(BusSchedule, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10, help_text="e.g. L1, L2, U1, 14")
    deck = models.CharField(max_length=10, choices=DECK_CHOICES, default='LOWER')
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES, default='SEATER')
    is_ladies_only = models.BooleanField(default=False)
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ['deck', 'seat_number']
        constraints = [
            models.UniqueConstraint(fields=['schedule', 'seat_number'], name='unique_bus_seat_per_schedule')
        ]
        verbose_name = "Bus Seat"
        verbose_name_plural = "Bus Seats"

    def __str__(self):
        return f"{self.seat_number} ({self.get_deck_display()} - {self.get_seat_type_display()})"
