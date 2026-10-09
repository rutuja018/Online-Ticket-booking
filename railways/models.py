from django.db import models
from django.utils import timezone
from decimal import Decimal

class RailwayStation(models.Model):
    code = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['city', 'name']
        verbose_name = "Railway Station"
        verbose_name_plural = "Railway Stations"

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.city}"


class Train(models.Model):
    TRAIN_TYPE_CHOICES = (
        ('VANDE_BHARAT', 'Vande Bharat Express'),
        ('RAJDHANI', 'Rajdhani Express'),
        ('SHATABDI', 'Shatabdi Express'),
        ('DURONTO', 'Duronto Express'),
        ('SUPERFAST', 'Superfast Express'),
        ('EXPRESS', 'Mail / Express'),
    )

    train_number = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    train_type = models.CharField(max_length=30, choices=TRAIN_TYPE_CHOICES, default='SUPERFAST')
    total_coaches = models.PositiveIntegerField(default=16)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['train_number']
        verbose_name = "Train"
        verbose_name_plural = "Trains"

    def __str__(self):
        return f"{self.train_number} - {self.name} ({self.get_train_type_display()})"


class TrainSchedule(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='schedules')
    source_station = models.ForeignKey(
        RailwayStation, on_delete=models.CASCADE, related_name='departing_trains'
    )
    destination_station = models.ForeignKey(
        RailwayStation, on_delete=models.CASCADE, related_name='arriving_trains'
    )
    journey_date = models.DateField(db_index=True)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    
    # Base Fares per class
    fare_general = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('180.00'))
    fare_sleeper = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('480.00'))
    fare_ac3 = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1250.00'))
    fare_ac2 = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1850.00'))
    fare_first_class = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('2950.00'))
    
    runs_on = models.CharField(max_length=100, default="Daily (All 7 Days)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['journey_date', 'departure_time']
        verbose_name = "Train Schedule"
        verbose_name_plural = "Train Schedules"

    def __str__(self):
        return f"{self.train.train_number} ({self.source_station.code} -> {self.destination_station.code}) on {self.journey_date}"

    @property
    def formatted_duration(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"

    def get_fare_for_class(self, travel_class):
        fares = {
            'GENERAL': self.fare_general,
            'SLEEPER': self.fare_sleeper,
            'AC_3_TIER': self.fare_ac3,
            'AC_2_TIER': self.fare_ac2,
            'FIRST_CLASS': self.fare_first_class,
        }
        return fares.get(travel_class, self.fare_sleeper)

    def available_seat_count(self, travel_class=None):
        if travel_class and not self.seats.filter(travel_class=travel_class).exists():
            self.generate_seats_for_class(travel_class)
        seats = self.seats.filter(is_booked=False)
        if travel_class:
            seats = seats.filter(travel_class=travel_class)
        return seats.count()

    def generate_seats_for_class(self, travel_class):
        if self.seats.filter(travel_class=travel_class).exists():
            return
        coaches = {'GENERAL': 'GEN1', 'SLEEPER': 'S1', 'AC_3_TIER': 'B1', 'AC_2_TIER': 'A1', 'FIRST_CLASS': 'H1'}
        coach_name = coaches.get(travel_class, 'S1')
        berths = ['LOWER', 'MIDDLE', 'UPPER', 'LOWER', 'MIDDLE', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER']
        new_seats = []
        for i in range(1, 41):
            b_type = berths[(i - 1) % len(berths)]
            new_seats.append(TrainSeat(
                schedule=self,
                coach=coach_name,
                seat_number=str(i),
                berth_type=b_type,
                travel_class=travel_class,
                is_booked=(i in [3, 7, 14, 22])
            ))
        TrainSeat.objects.bulk_create(new_seats, ignore_conflicts=True)


class TrainSeat(models.Model):
    CLASS_CHOICES = (
        ('GENERAL', 'General (2S)'),
        ('SLEEPER', 'Sleeper (SL)'),
        ('AC_3_TIER', 'AC 3 Tier (3A)'),
        ('AC_2_TIER', 'AC 2 Tier (2A)'),
        ('FIRST_CLASS', 'Executive / First AC (1A)'),
    )

    BERTH_CHOICES = (
        ('LOWER', 'Lower Berth'),
        ('MIDDLE', 'Middle Berth'),
        ('UPPER', 'Upper Berth'),
        ('SIDE_LOWER', 'Side Lower'),
        ('SIDE_UPPER', 'Side Upper'),
        ('CHAIR_CAR', 'Chair Car Window/Aisle'),
        ('CABIN', 'First AC Coupe/Cabin'),
    )

    schedule = models.ForeignKey(TrainSchedule, on_delete=models.CASCADE, related_name='seats')
    coach = models.CharField(max_length=10, help_text="Coach e.g. S1, B1, A1, H1, D1")
    seat_number = models.CharField(max_length=10, help_text="Seat or Berth No e.g. 12")
    berth_type = models.CharField(max_length=20, choices=BERTH_CHOICES, default='LOWER')
    travel_class = models.CharField(max_length=20, choices=CLASS_CHOICES, default='SLEEPER')
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ['coach', 'id']
        constraints = [
            models.UniqueConstraint(fields=['schedule', 'coach', 'seat_number'], name='unique_train_seat_per_schedule')
        ]
        verbose_name = "Train Seat"
        verbose_name_plural = "Train Seats"

    def __str__(self):
        return f"{self.coach}-{self.seat_number} ({self.get_travel_class_display()} - {self.get_berth_type_display()})"
