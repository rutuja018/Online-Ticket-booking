from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time, datetime

from railways.models import RailwayStation, Train, TrainSchedule, TrainSeat
from airlines.models import Airport, Airline, Aircraft, Flight, FlightSchedule, FlightSeat
from buses.models import BusOperator, Bus, BusRoute, BusSchedule, BusSeat
from bookings.models import Booking, Passenger
from payments.models import Payment

class RailAwayEndToEndTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        self.future_date = self.today + timedelta(days=2)

        # 1. Users
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword',
            first_name='Super',
            last_name='Admin'
        )

        # 2. Railway setup
        self.station_a = RailwayStation.objects.create(code='DEL', name='New Delhi', city='Delhi', state='Delhi')
        self.station_b = RailwayStation.objects.create(code='MUM', name='Mumbai Central', city='Mumbai', state='Maharashtra')
        self.train = Train.objects.create(train_number='12952', name='Rajdhani Express', train_type='RAJDHANI')
        self.train_schedule = TrainSchedule.objects.create(
            train=self.train,
            source_station=self.station_a,
            destination_station=self.station_b,
            journey_date=self.future_date,
            departure_time=time(16, 30),
            arrival_time=time(8, 30),
            duration_minutes=960,
            fare_sleeper=Decimal('500.00'),
            fare_ac3=Decimal('1500.00')
        )
        self.train_seat_1 = TrainSeat.objects.create(
            schedule=self.train_schedule,
            coach='B1',
            seat_number='1',
            berth_type='LOWER',
            travel_class='AC_3_TIER',
            is_booked=False
        )
        self.train_seat_2 = TrainSeat.objects.create(
            schedule=self.train_schedule,
            coach='B1',
            seat_number='2',
            berth_type='UPPER',
            travel_class='AC_3_TIER',
            is_booked=False
        )

        # 3. Flight setup
        self.airport_a = Airport.objects.create(code='DEL', name='Indira Gandhi Airport', city='Delhi')
        self.airport_b = Airport.objects.create(code='BOM', name='Mumbai Airport', city='Mumbai')
        self.airline = Airline.objects.create(code='6E', name='IndiGo')
        self.flight = Flight.objects.create(flight_number='6E-101', airline=self.airline)
        dep_dt = timezone.make_aware(datetime.combine(self.future_date, time(10, 0)))
        arr_dt = dep_dt + timedelta(hours=2)
        self.flight_schedule = FlightSchedule.objects.create(
            flight=self.flight,
            origin_airport=self.airport_a,
            destination_airport=self.airport_b,
            departure_datetime=dep_dt,
            arrival_datetime=arr_dt,
            duration_minutes=120,
            fare_economy=Decimal('4000.00')
        )
        self.flight_seat = FlightSeat.objects.create(
            schedule=self.flight_schedule,
            seat_number='12A',
            row_number=12,
            column_letter='A',
            cabin_class='ECONOMY',
            is_booked=False
        )

        # 4. Bus setup
        self.operator = BusOperator.objects.create(name='Zingbus')
        self.bus = Bus.objects.create(bus_number='DL-01-2024', operator=self.operator, bus_type='VOLVO')
        self.bus_route = BusRoute.objects.create(
            source_city='Delhi', destination_city='Jaipur', boarding_points='ISBT', dropping_points='Sindhi Camp'
        )
        self.bus_schedule = BusSchedule.objects.create(
            bus=self.bus,
            route=self.bus_route,
            journey_date=self.future_date,
            departure_time=time(6, 0),
            arrival_time=time(11, 0),
            duration_minutes=300,
            base_fare=Decimal('600.00')
        )
        self.bus_seat = BusSeat.objects.create(
            schedule=self.bus_schedule,
            seat_number='L1',
            deck='LOWER',
            is_booked=False
        )

    def test_user_registration_and_login(self):
        """Test registration and authentication"""
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'New',
            'last_name': 'Traveler',
            'username': 'newtraveler',
            'email': 'new@traveler.com',
            'phone': '9988776655',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newtraveler').exists())

        # Test login
        self.client.logout()
        login_resp = self.client.post(reverse('accounts:login'), {
            'username': 'newtraveler',
            'password': 'StrongPassword123'
        })
        self.assertEqual(login_resp.status_code, 302)

    def test_railway_search(self):
        """Test searching trains by station and date"""
        response = self.client.get(reverse('railways:search'), {
            'from_station': self.station_a.id,
            'to_station': self.station_b.id,
            'journey_date': self.future_date.isoformat(),
            'travel_class': 'AC_3_TIER'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rajdhani Express')

    def test_flight_search(self):
        """Test searching flights by airport"""
        response = self.client.get(reverse('airlines:search'), {
            'from_airport': self.airport_a.id,
            'to_airport': self.airport_b.id,
            'departure_date': self.future_date.isoformat(),
            'cabin_class': 'ECONOMY'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '6E-101')

    def test_bus_search(self):
        """Test searching buses by city"""
        response = self.client.get(reverse('buses:search'), {
            'from_city': 'Delhi',
            'to_city': 'Jaipur',
            'travel_date': self.future_date.isoformat()
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zingbus')

    def test_end_to_end_train_booking_and_payment(self):
        """Test complete booking flow: seat selection -> booking create -> payment -> confirmed PNR"""
        self.client.login(username='testuser', password='password123')

        # 1. Create booking for 2 seats (B1-1, B1-2)
        create_resp = self.client.post(reverse('bookings:create'), {
            'transport_type': 'TRAIN',
            'schedule_id': self.train_schedule.id,
            'travel_class': 'AC_3_TIER',
            'selected_seats': 'B1-1, B1-2',
            'promo_code': 'RAILAWAY100',
            'passenger_1_name': 'Passenger One',
            'passenger_1_age': '30',
            'passenger_1_gender': 'MALE',
            'passenger_1_id_type': 'AADHAAR',
            'passenger_1_id_number': '123456789012',
            'passenger_2_name': 'Passenger Two',
            'passenger_2_age': '28',
            'passenger_2_gender': 'FEMALE',
            'passenger_2_id_type': 'PASSPORT',
            'passenger_2_id_number': 'Z9876543',
        })
        self.assertEqual(create_resp.status_code, 302)

        booking = Booking.objects.filter(user=self.user).order_by('-created_at').first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.passenger_count, 2)
        self.assertEqual(booking.booking_status, 'PENDING')
        # Base Fare = 1500 * 2 = 3000, Tax = 5% of 3000 = 150, Fee = 49, Discount = 100 => Total = 3099
        self.assertEqual(booking.total_amount, Decimal('3099.00'))

        # 2. Process Demo Payment
        pay_resp = self.client.post(reverse('payments:process_payment', kwargs={'booking_id': booking.id}), {
            'payment_method': 'CREDIT_CARD',
            'card_number': '4242 4242 4242 4242',
            'simulate_action': 'SUCCESS'
        })
        self.assertEqual(pay_resp.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, 'CONFIRMED')
        self.assertEqual(booking.payment_status, 'SUCCESS')
        self.assertTrue(hasattr(booking, 'payment'))

        # Seats must now be marked is_booked=True
        self.train_seat_1.refresh_from_db()
        self.train_seat_2.refresh_from_db()
        self.assertTrue(self.train_seat_1.is_booked)
        self.assertTrue(self.train_seat_2.is_booked)

    def test_cancellation_and_seat_release(self):
        """Test cancelling a confirmed booking releases seats and updates refund"""
        self.client.login(username='testuser', password='password123')

        booking = Booking.objects.create(
            user=self.user,
            transport_type='TRAIN',
            train_schedule=self.train_schedule,
            service_title='Rajdhani Express',
            travel_class='AC_3_TIER',
            source_location='Delhi',
            destination_location='Mumbai',
            journey_date=self.future_date,
            departure_time='16:30',
            arrival_time='08:30',
            passenger_count=1,
            allocated_seats='B1-1',
            base_fare=Decimal('1500.00'),
            taxes=Decimal('75.00'),
            service_fee=Decimal('49.00'),
            total_amount=Decimal('1624.00'),
            booking_status='CONFIRMED',
            payment_status='SUCCESS'
        )
        self.train_seat_1.is_booked = True
        self.train_seat_1.save()

        # Perform cancellation
        cancel_resp = self.client.post(reverse('bookings:cancel', kwargs={'pnr': booking.pnr}), {
            'cancellation_reason': 'Trip plan rescheduled'
        })
        self.assertEqual(cancel_resp.status_code, 302)

        booking.refresh_from_db()
        self.assertEqual(booking.booking_status, 'CANCELLED')
        self.assertEqual(booking.payment_status, 'REFUNDED')
        self.assertGreater(booking.refund_amount, Decimal('0.00'))

        # Verify seat was released back to false
        self.train_seat_1.refresh_from_db()
        self.assertFalse(self.train_seat_1.is_booked)

    def test_admin_dashboard_security(self):
        """Test standard customer cannot access admin dashboard, but admin can"""
        self.client.login(username='testuser', password='password123')
        cust_resp = self.client.get(reverse('admin_dashboard:home'))
        # Should redirect or reject
        self.assertNotEqual(cust_resp.status_code, 200)

        self.client.login(username='adminuser', password='adminpassword')
        admin_resp = self.client.get(reverse('admin_dashboard:home'))
        self.assertEqual(admin_resp.status_code, 200)
        self.assertContains(admin_resp, 'Analytics & Platform Overview')
