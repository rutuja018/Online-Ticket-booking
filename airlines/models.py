from django.db import models
from decimal import Decimal

class Airport(models.Model):
    code = models.CharField(max_length=10, unique=True, db_index=True, help_text="IATA 3-letter code e.g. DEL, BOM")
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, default="India")
    terminal = models.CharField(max_length=50, default="Terminal 1 / 2")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['city', 'name']
        verbose_name = "Airport"
        verbose_name_plural = "Airports"

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.city}"


class Airline(models.Model):
    code = models.CharField(max_length=10, unique=True, db_index=True, help_text="e.g. AI, 6E, UK, SG, QP")
    name = models.CharField(max_length=100)
    logo_icon = models.CharField(max_length=50, default="fa-plane")
    callsign = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Airline"
        verbose_name_plural = "Airlines"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Aircraft(models.Model):
    model_name = models.CharField(max_length=100, help_text="e.g. Airbus A320neo, Boeing 737 MAX 8, Boeing 787-9")
    total_capacity = models.PositiveIntegerField(default=180)

    def __str__(self):
        return f"{self.model_name} ({self.total_capacity} Seats)"


class Flight(models.Model):
    flight_number = models.CharField(max_length=20, unique=True, db_index=True, help_text="e.g. 6E-2041, AI-805")
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, related_name='flights')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.SET_NULL, null=True, blank=True, related_name='flights')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['flight_number']
        verbose_name = "Flight"
        verbose_name_plural = "Flights"

    def __str__(self):
        return f"{self.airline.name} {self.flight_number}"


class FlightSchedule(models.Model):
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='schedules')
    origin_airport = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name='departing_flights'
    )
    destination_airport = models.ForeignKey(
        Airport, on_delete=models.CASCADE, related_name='arriving_flights'
    )
    departure_datetime = models.DateTimeField(db_index=True)
    arrival_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(help_text="Flight duration in minutes")
    stops = models.PositiveIntegerField(default=0, help_text="0 for Non-stop, 1 for 1 stop")
    
    # Fare breakdown
    fare_economy = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal('4200.00'))
    fare_premium_economy = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal('6800.00'))
    fare_business = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal('14500.00'))
    fare_first_class = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal('26000.00'))
    
    baggage_allowance = models.CharField(max_length=100, default="15 Kg Check-in + 7 Kg Cabin")
    meal_included = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['departure_datetime']
        verbose_name = "Flight Schedule"
        verbose_name_plural = "Flight Schedules"

    def __str__(self):
        return f"{self.flight.flight_number} ({self.origin_airport.code} -> {self.destination_airport.code}) at {self.departure_datetime.strftime('%Y-%m-%d %H:%M')}"

    @property
    def formatted_duration(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"

    def get_fare_for_class(self, travel_class):
        fares = {
            'ECONOMY': self.fare_economy,
            'PREMIUM_ECONOMY': self.fare_premium_economy,
            'BUSINESS': self.fare_business,
            'FIRST_CLASS': self.fare_first_class,
        }
        return fares.get(travel_class, self.fare_economy)

    def available_seat_count(self, travel_class=None):
        if travel_class and not self.seats.filter(cabin_class=travel_class).exists():
            self.generate_seats_for_class(travel_class)
        seats = self.seats.filter(is_booked=False)
        if travel_class:
            seats = seats.filter(cabin_class=travel_class)
        return seats.count()

    def generate_seats_for_class(self, cabin_class):
        """Generates realistic seats for the specified cabin class if none exist."""
        if self.seats.filter(cabin_class=cabin_class).exists():
            return
        new_seats = []
        if cabin_class == 'FIRST_CLASS':
            for r in [1, 2]:
                for c in ['A', 'B', 'E', 'F']:
                    st = 'WINDOW' if c in ['A', 'F'] else 'AISLE'
                    new_seats.append(FlightSeat(
                        schedule=self,
                        seat_number=f"{r}{c}",
                        row_number=r,
                        column_letter=c,
                        cabin_class='FIRST_CLASS',
                        seat_type=st,
                        is_booked=(r == 1 and c == 'B')
                    ))
        elif cabin_class == 'BUSINESS':
            for r in range(3, 6):
                for c in ['A', 'C', 'D', 'F']:
                    st = 'WINDOW' if c in ['A', 'F'] else 'AISLE'
                    new_seats.append(FlightSeat(
                        schedule=self,
                        seat_number=f"{r}{c}",
                        row_number=r,
                        column_letter=c,
                        cabin_class='BUSINESS',
                        seat_type=st,
                        is_booked=(r == 3 and c == 'A')
                    ))
        elif cabin_class == 'PREMIUM_ECONOMY':
            for r in range(6, 10):
                for c in ['A', 'B', 'C', 'D', 'E', 'F']:
                    st = 'EXTRA_LEGROOM' if c in ['A', 'F'] else ('AISLE' if c in ['C', 'D'] else 'MIDDLE')
                    new_seats.append(FlightSeat(
                        schedule=self,
                        seat_number=f"{r}{c}",
                        row_number=r,
                        column_letter=c,
                        cabin_class='PREMIUM_ECONOMY',
                        seat_type=st,
                        is_booked=(r == 7 and c == 'C')
                    ))
        else:  # ECONOMY
            for r in range(10, 26):
                for c in ['A', 'B', 'C', 'D', 'E', 'F']:
                    st = 'WINDOW' if c in ['A', 'F'] else ('AISLE' if c in ['C', 'D'] else 'MIDDLE')
                    new_seats.append(FlightSeat(
                        schedule=self,
                        seat_number=f"{r}{c}",
                        row_number=r,
                        column_letter=c,
                        cabin_class='ECONOMY',
                        seat_type=st,
                        is_booked=(r in [12, 18] and c in ['A', 'F'])
                    ))
        if new_seats:
            FlightSeat.objects.bulk_create(new_seats, ignore_conflicts=True)


class FlightSeat(models.Model):
    CABIN_CHOICES = (
        ('ECONOMY', 'Economy Class'),
        ('PREMIUM_ECONOMY', 'Premium Economy'),
        ('BUSINESS', 'Business Class'),
        ('FIRST_CLASS', 'First Class Suite'),
    )

    SEAT_TYPE_CHOICES = (
        ('WINDOW', 'Window Seat'),
        ('AISLE', 'Aisle Seat'),
        ('MIDDLE', 'Middle Seat'),
        ('EXTRA_LEGROOM', 'Extra Legroom'),
    )

    schedule = models.ForeignKey(FlightSchedule, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10, help_text="e.g. 1A, 12F, 24C")
    row_number = models.PositiveIntegerField()
    column_letter = models.CharField(max_length=2)
    cabin_class = models.CharField(max_length=20, choices=CABIN_CHOICES, default='ECONOMY')
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPE_CHOICES, default='AISLE')
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ['row_number', 'column_letter']
        constraints = [
            models.UniqueConstraint(fields=['schedule', 'seat_number'], name='unique_flight_seat_per_schedule')
        ]
        verbose_name = "Flight Seat"
        verbose_name_plural = "Flight Seats"

    def __str__(self):
        return f"{self.seat_number} ({self.get_cabin_class_display()} - {self.get_seat_type_display()})"
