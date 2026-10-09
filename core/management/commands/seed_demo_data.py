import random
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import UserProfile
from railways.models import RailwayStation, Train, TrainSchedule, TrainSeat
from airlines.models import Airport, Airline, Aircraft, Flight, FlightSchedule, FlightSeat
from buses.models import BusOperator, Bus, BusRoute, BusSchedule, BusSeat
from bookings.models import Booking, Passenger
from payments.models import Payment
from food_catering.models import StationRestaurant, FoodCategory, FoodItem, FoodOrder, FoodOrderItem
from retiring_rooms.models import StationRetiringRoom, RetiringRoomBooking
from experiences.models import CustomerReview, ReviewHelpfulVote

class Command(BaseCommand):
    help = 'Seeds realistic sample demo data for Railways, Airlines, Buses, Users, and Sample Bookings'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting RailAway database seeding..."))

        today = timezone.now().date()

        # ==========================================
        # 1. USERS & PROFILES
        # ==========================================
        self.stdout.write("Creating demo users...")
        
        # Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@railaway.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        if hasattr(admin_user, 'profile'):
            admin_user.profile.role = 'ADMIN'
            admin_user.profile.phone = '+91 9876543210'
            admin_user.profile.city = 'New Delhi'
            admin_user.profile.save()

        # Demo Customer User
        customer_user, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@railaway.com',
                'first_name': 'Rohan',
                'last_name': 'Sharma',
            }
        )
        customer_user.set_password('password123')
        customer_user.save()
        if hasattr(customer_user, 'profile'):
            customer_user.profile.role = 'CUSTOMER'
            customer_user.profile.phone = '+91 9811223344'
            customer_user.profile.city = 'Mumbai'
            customer_user.profile.address = 'Flat 402, Sea View Residency, Bandra West'
            customer_user.profile.state = 'Maharashtra'
            customer_user.profile.pincode = '400050'
            customer_user.profile.save()

        # Another Customer User
        ananya_user, _ = User.objects.get_or_create(
            username='ananya',
            defaults={
                'email': 'ananya.p@example.com',
                'first_name': 'Ananya',
                'last_name': 'Patel',
            }
        )
        ananya_user.set_password('password123')
        ananya_user.save()

        # ==========================================
        # 2. RAILWAYS SEEDING
        # ==========================================
        self.stdout.write("Seeding Railway stations, trains, schedules & berths...")

        stations_data = [
            # Northern & NCR
            {'code': 'NDLS', 'name': 'New Delhi Railway Station', 'city': 'New Delhi', 'state': 'Delhi'},
            {'code': 'DLI', 'name': 'Old Delhi Junction', 'city': 'Delhi', 'state': 'Delhi'},
            {'code': 'NZM', 'name': 'Hazrat Nizamuddin', 'city': 'New Delhi', 'state': 'Delhi'},
            {'code': 'ANVT', 'name': 'Anand Vihar Terminal', 'city': 'New Delhi', 'state': 'Delhi'},
            {'code': 'LKO', 'name': 'Lucknow Charbagh NR', 'city': 'Lucknow', 'state': 'Uttar Pradesh'},
            {'code': 'BSB', 'name': 'Varanasi Junction', 'city': 'Varanasi', 'state': 'Uttar Pradesh'},
            {'code': 'AYC', 'name': 'Ayodhya Cantt Junction', 'city': 'Ayodhya', 'state': 'Uttar Pradesh'},
            {'code': 'PRYJ', 'name': 'Prayagraj Junction', 'city': 'Prayagraj', 'state': 'Uttar Pradesh'},
            {'code': 'CNB', 'name': 'Kanpur Central', 'city': 'Kanpur', 'state': 'Uttar Pradesh'},
            {'code': 'AGC', 'name': 'Agra Cantt', 'city': 'Agra', 'state': 'Uttar Pradesh'},
            {'code': 'CDG', 'name': 'Chandigarh Junction', 'city': 'Chandigarh', 'state': 'Chandigarh'},
            {'code': 'ASR', 'name': 'Amritsar Junction', 'city': 'Amritsar', 'state': 'Punjab'},
            {'code': 'JAT', 'name': 'Jammu Tawi', 'city': 'Jammu', 'state': 'Jammu & Kashmir'},
            {'code': 'DDN', 'name': 'Dehradun Terminal', 'city': 'Dehradun', 'state': 'Uttarakhand'},
            {'code': 'HW', 'name': 'Haridwar Junction', 'city': 'Haridwar', 'state': 'Uttarakhand'},
            {'code': 'KLK', 'name': 'Kalka Railway Station', 'city': 'Shimla', 'state': 'Himachal Pradesh'},

            # Western & Central
            {'code': 'MMCT', 'name': 'Mumbai Central', 'city': 'Mumbai', 'state': 'Maharashtra'},
            {'code': 'BOM', 'name': 'Mumbai Central (Main)', 'city': 'Mumbai', 'state': 'Maharashtra'},
            {'code': 'CSMT', 'name': 'Chhatrapati Shivaji Maharaj Terminus', 'city': 'Mumbai', 'state': 'Maharashtra'},
            {'code': 'BDTS', 'name': 'Bandra Terminus', 'city': 'Mumbai', 'state': 'Maharashtra'},
            {'code': 'PUNE', 'name': 'Pune Junction', 'city': 'Pune', 'state': 'Maharashtra'},
            {'code': 'NGP', 'name': 'Nagpur Junction', 'city': 'Nagpur', 'state': 'Maharashtra'},
            {'code': 'ADI', 'name': 'Ahmedabad Junction', 'city': 'Ahmedabad', 'state': 'Gujarat'},
            {'code': 'BRC', 'name': 'Vadodara Junction', 'city': 'Vadodara', 'state': 'Gujarat'},
            {'code': 'ST', 'name': 'Surat Railway Station', 'city': 'Surat', 'state': 'Gujarat'},
            {'code': 'JP', 'name': 'Jaipur Junction', 'city': 'Jaipur', 'state': 'Rajasthan'},
            {'code': 'JU', 'name': 'Jodhpur Junction', 'city': 'Jodhpur', 'state': 'Rajasthan'},
            {'code': 'UDZ', 'name': 'Udaipur City', 'city': 'Udaipur', 'state': 'Rajasthan'},
            {'code': 'KOTA', 'name': 'Kota Junction', 'city': 'Kota', 'state': 'Rajasthan'},
            {'code': 'MAO', 'name': 'Madgaon Junction Goa', 'city': 'Goa', 'state': 'Goa'},
            {'code': 'KRMI', 'name': 'Karmali Railway Station', 'city': 'Goa', 'state': 'Goa'},

            # Southern
            {'code': 'SBC', 'name': 'KSR Bengaluru City Junction', 'city': 'Bengaluru', 'state': 'Karnataka'},
            {'code': 'YPR', 'name': 'Yesvantpur Junction', 'city': 'Bengaluru', 'state': 'Karnataka'},
            {'code': 'MYS', 'name': 'Mysuru Junction', 'city': 'Mysuru', 'state': 'Karnataka'},
            {'code': 'MAQ', 'name': 'Mangaluru Central', 'city': 'Mangaluru', 'state': 'Karnataka'},
            {'code': 'MAS', 'name': 'Puratchi Thalaivar Dr. M.G.R. Chennai Central', 'city': 'Chennai', 'state': 'Tamil Nadu'},
            {'code': 'MS', 'name': 'Chennai Egmore', 'city': 'Chennai', 'state': 'Tamil Nadu'},
            {'code': 'CBE', 'name': 'Coimbatore Junction', 'city': 'Coimbatore', 'state': 'Tamil Nadu'},
            {'code': 'MDU', 'name': 'Madurai Junction', 'city': 'Madurai', 'state': 'Tamil Nadu'},
            {'code': 'HYB', 'name': 'Hyderabad Deccan Nampally', 'city': 'Hyderabad', 'state': 'Telangana'},
            {'code': 'SC', 'name': 'Secunderabad Junction', 'city': 'Hyderabad', 'state': 'Telangana'},
            {'code': 'TPTY', 'name': 'Tirupati Main', 'city': 'Tirupati', 'state': 'Andhra Pradesh'},
            {'code': 'BZA', 'name': 'Vijayawada Junction', 'city': 'Vijayawada', 'state': 'Andhra Pradesh'},
            {'code': 'VSKP', 'name': 'Visakhapatnam Junction', 'city': 'Visakhapatnam', 'state': 'Andhra Pradesh'},
            {'code': 'ERS', 'name': 'Ernakulam Junction (Kochi)', 'city': 'Kochi', 'state': 'Kerala'},
            {'code': 'TVC', 'name': 'Thiruvananthapuram Central', 'city': 'Thiruvananthapuram', 'state': 'Kerala'},
            {'code': 'CLT', 'name': 'Kozhikode Main', 'city': 'Kozhikode', 'state': 'Kerala'},

            # Eastern & Central
            {'code': 'HWH', 'name': 'Howrah Junction', 'city': 'Kolkata', 'state': 'West Bengal'},
            {'code': 'SDAH', 'name': 'Sealdah Terminal', 'city': 'Kolkata', 'state': 'West Bengal'},
            {'code': 'KOAA', 'name': 'Kolkata Railway Station', 'city': 'Kolkata', 'state': 'West Bengal'},
            {'code': 'PNBE', 'name': 'Patna Junction', 'city': 'Patna', 'state': 'Bihar'},
            {'code': 'GAYA', 'name': 'Gaya Junction', 'city': 'Gaya', 'state': 'Bihar'},
            {'code': 'BBS', 'name': 'Bhubaneswar Junction', 'city': 'Bhubaneswar', 'state': 'Odisha'},
            {'code': 'PURI', 'name': 'Puri Railway Station', 'city': 'Puri', 'state': 'Odisha'},
            {'code': 'GHY', 'name': 'Guwahati Junction', 'city': 'Guwahati', 'state': 'Assam'},
            {'code': 'R', 'name': 'Raipur Junction', 'city': 'Raipur', 'state': 'Chhattisgarh'},
            {'code': 'RNC', 'name': 'Ranchi Junction', 'city': 'Ranchi', 'state': 'Jharkhand'},
            {'code': 'BPL', 'name': 'Bhopal Junction', 'city': 'Bhopal', 'state': 'Madhya Pradesh'},
            {'code': 'INDB', 'name': 'Indore Junction', 'city': 'Indore', 'state': 'Madhya Pradesh'},
            {'code': 'GWL', 'name': 'Gwalior Junction', 'city': 'Gwalior', 'state': 'Madhya Pradesh'},
            {'code': 'JBP', 'name': 'Jabalpur Junction', 'city': 'Jabalpur', 'state': 'Madhya Pradesh'},
        ]

        stations_dict = {}
        for s in stations_data:
            stn, _ = RailwayStation.objects.get_or_create(code=s['code'], defaults=s)
            stations_dict[s['code']] = stn

        trains_data = [
            {'train_number': '22436', 'name': 'Vande Bharat Express', 'train_type': 'VANDE_BHARAT', 'total_coaches': 16},
            {'train_number': '20901', 'name': 'Vande Bharat Express (Mumbai - Gandhinagar)', 'train_type': 'VANDE_BHARAT', 'total_coaches': 16},
            {'train_number': '20607', 'name': 'Vande Bharat Express (Chennai - Mysuru)', 'train_type': 'VANDE_BHARAT', 'total_coaches': 16},
            {'train_number': '22458', 'name': 'Vande Bharat Express (Dehradun - Delhi)', 'train_type': 'VANDE_BHARAT', 'total_coaches': 16},
            {'train_number': '12952', 'name': 'Mumbai Rajdhani Express', 'train_type': 'RAJDHANI', 'total_coaches': 20},
            {'train_number': '12424', 'name': 'Dibrugarh Rajdhani Express', 'train_type': 'RAJDHANI', 'total_coaches': 20},
            {'train_number': '22692', 'name': 'Bengaluru Rajdhani Express', 'train_type': 'RAJDHANI', 'total_coaches': 20},
            {'train_number': '12004', 'name': 'Lucknow Swarna Shatabdi', 'train_type': 'SHATABDI', 'total_coaches': 14},
            {'train_number': '12015', 'name': 'Ajmer Shatabdi Express', 'train_type': 'SHATABDI', 'total_coaches': 14},
            {'train_number': '12019', 'name': 'Howrah Ranchi Shatabdi', 'train_type': 'SHATABDI', 'total_coaches': 14},
            {'train_number': '12260', 'name': 'Sealdah Duronto Express', 'train_type': 'DURONTO', 'total_coaches': 18},
            {'train_number': '12213', 'name': 'Yesvantpur Delhi Sarai Duronto', 'train_type': 'DURONTO', 'total_coaches': 18},
            {'train_number': '12626', 'name': 'Kerala Superfast Express', 'train_type': 'SUPERFAST', 'total_coaches': 22},
            {'train_number': '12124', 'name': 'Deccan Queen Superfast', 'train_type': 'SUPERFAST', 'total_coaches': 16},
            {'train_number': '12903', 'name': 'Golden Temple Mail', 'train_type': 'EXPRESS', 'total_coaches': 22},
            {'train_number': '12617', 'name': 'Mangala Lakshadweep Superfast', 'train_type': 'SUPERFAST', 'total_coaches': 22},
            {'train_number': '12801', 'name': 'Purushottam Superfast Express', 'train_type': 'SUPERFAST', 'total_coaches': 22},
        ]

        trains_dict = {}
        for t in trains_data:
            tr, _ = Train.objects.get_or_create(train_number=t['train_number'], defaults=t)
            trains_dict[t['train_number']] = tr

        # Train Schedules across multiple dates
        train_schedules_specs = [
            {
                'train': '22436', 'src': 'NDLS', 'dst': 'BSB', 'dep': time(6, 0), 'arr': time(14, 0),
                'dur': 480, 'gen': Decimal('450.00'), 'sl': Decimal('750.00'), 'ac3': Decimal('1650.00'),
                'ac2': Decimal('2450.00'), 'ac1': Decimal('3250.00')
            },
            {
                'train': '22436', 'src': 'BSB', 'dst': 'NDLS', 'dep': time(15, 0), 'arr': time(23, 0),
                'dur': 480, 'gen': Decimal('450.00'), 'sl': Decimal('750.00'), 'ac3': Decimal('1650.00'),
                'ac2': Decimal('2450.00'), 'ac1': Decimal('3250.00')
            },
            {
                'train': '12952', 'src': 'NDLS', 'dst': 'BOM', 'dep': time(16, 55), 'arr': time(8, 35),
                'dur': 940, 'gen': Decimal('320.00'), 'sl': Decimal('890.00'), 'ac3': Decimal('2250.00'),
                'ac2': Decimal('3180.00'), 'ac1': Decimal('4950.00')
            },
            {
                'train': '12952', 'src': 'BOM', 'dst': 'NDLS', 'dep': time(17, 0), 'arr': time(8, 30),
                'dur': 930, 'gen': Decimal('320.00'), 'sl': Decimal('890.00'), 'ac3': Decimal('2250.00'),
                'ac2': Decimal('3180.00'), 'ac1': Decimal('4950.00')
            },
            {
                'train': '12004', 'src': 'NDLS', 'dst': 'LKO', 'dep': time(6, 10), 'arr': time(12, 40),
                'dur': 390, 'gen': Decimal('240.00'), 'sl': Decimal('520.00'), 'ac3': Decimal('1150.00'),
                'ac2': Decimal('1750.00'), 'ac1': Decimal('2450.00')
            },
            {
                'train': '12004', 'src': 'LKO', 'dst': 'NDLS', 'dep': time(15, 35), 'arr': time(22, 10),
                'dur': 395, 'gen': Decimal('240.00'), 'sl': Decimal('520.00'), 'ac3': Decimal('1150.00'),
                'ac2': Decimal('1750.00'), 'ac1': Decimal('2450.00')
            },
            {
                'train': '22692', 'src': 'NDLS', 'dst': 'SBC', 'dep': time(20, 20), 'arr': time(5, 20),
                'dur': 2040, 'gen': Decimal('480.00'), 'sl': Decimal('1150.00'), 'ac3': Decimal('2850.00'),
                'ac2': Decimal('4100.00'), 'ac1': Decimal('6200.00')
            },
            {
                'train': '22692', 'src': 'SBC', 'dst': 'NDLS', 'dep': time(20, 0), 'arr': time(5, 30),
                'dur': 2010, 'gen': Decimal('480.00'), 'sl': Decimal('1150.00'), 'ac3': Decimal('2850.00'),
                'ac2': Decimal('4100.00'), 'ac1': Decimal('6200.00')
            },
            {
                'train': '12124', 'src': 'PUNE', 'dst': 'BOM', 'dep': time(7, 15), 'arr': time(10, 25),
                'dur': 190, 'gen': Decimal('120.00'), 'sl': Decimal('250.00'), 'ac3': Decimal('550.00'),
                'ac2': Decimal('850.00'), 'ac1': Decimal('1350.00')
            },
            {
                'train': '12124', 'src': 'BOM', 'dst': 'PUNE', 'dep': time(17, 10), 'arr': time(20, 25),
                'dur': 195, 'gen': Decimal('120.00'), 'sl': Decimal('250.00'), 'ac3': Decimal('550.00'),
                'ac2': Decimal('850.00'), 'ac1': Decimal('1350.00')
            },
            {
                'train': '12260', 'src': 'NDLS', 'dst': 'HWH', 'dep': time(19, 45), 'arr': time(12, 45),
                'dur': 1020, 'gen': Decimal('360.00'), 'sl': Decimal('920.00'), 'ac3': Decimal('2450.00'),
                'ac2': Decimal('3450.00'), 'ac1': Decimal('5200.00')
            },
        ]

        # Generate for past 3 days and next 35 days ahead
        for day_offset in range(-3, 36):
            j_date = today + timedelta(days=day_offset)
            for spec in train_schedules_specs:
                sched, sched_created = TrainSchedule.objects.get_or_create(
                    train=trains_dict[spec['train']],
                    source_station=stations_dict[spec['src']],
                    destination_station=stations_dict[spec['dst']],
                    journey_date=j_date,
                    defaults={
                        'departure_time': spec['dep'],
                        'arrival_time': spec['arr'],
                        'duration_minutes': spec['dur'],
                        'fare_general': spec['gen'],
                        'fare_sleeper': spec['sl'],
                        'fare_ac3': spec['ac3'],
                        'fare_ac2': spec['ac2'],
                        'fare_first_class': spec['ac1'],
                    }
                )

                if sched_created:
                    # Generate train seats for this schedule
                    coach_configs = [
                        ('GEN1', 'GENERAL', ['CHAIR_CAR'], 20),
                        ('S1', 'SLEEPER', ['LOWER', 'MIDDLE', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER'], 32),
                        ('B1', 'AC_3_TIER', ['LOWER', 'MIDDLE', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER'], 32),
                        ('A1', 'AC_2_TIER', ['LOWER', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER'], 24),
                        ('H1', 'FIRST_CLASS', ['CABIN', 'COUPE'], 12),
                    ]
                    seat_objs = []
                    for coach, t_class, b_types, seat_count in coach_configs:
                        for s_num in range(1, seat_count + 1):
                            b_type = b_types[(s_num - 1) % len(b_types)]
                            is_booked = (s_num in [3, 8, 15, 21]) # sample booked seats
                            seat_objs.append(TrainSeat(
                                schedule=sched,
                                coach=coach,
                                seat_number=str(s_num),
                                berth_type=b_type,
                                travel_class=t_class,
                                is_booked=is_booked
                            ))
                    TrainSeat.objects.bulk_create(seat_objs)

        # ==========================================
        # 3. AIRLINES SEEDING
        # ==========================================
        self.stdout.write("Seeding Airports, Airlines, Aircraft, Flights & cabin seat maps...")

        airports_data = [
            # Top Metro & International
            {'code': 'DEL', 'name': 'Indira Gandhi International Airport', 'city': 'New Delhi', 'country': 'India', 'terminal': 'Terminal 3'},
            {'code': 'BOM', 'name': 'Chhatrapati Shivaji Maharaj International', 'city': 'Mumbai', 'country': 'India', 'terminal': 'Terminal 2'},
            {'code': 'BLR', 'name': 'Kempegowda International Airport', 'city': 'Bengaluru', 'country': 'India', 'terminal': 'Terminal 1 & 2'},
            {'code': 'MAA', 'name': 'Chennai International Airport', 'city': 'Chennai', 'country': 'India', 'terminal': 'Terminal 1'},
            {'code': 'CCU', 'name': 'Netaji Subhash Chandra Bose International', 'city': 'Kolkata', 'country': 'India', 'terminal': 'Terminal 1'},
            {'code': 'HYD', 'name': 'Rajiv Gandhi International Airport', 'city': 'Hyderabad', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'GOI', 'name': 'Dabolim Goa International Airport', 'city': 'Goa', 'country': 'India', 'terminal': 'Terminal 1'},
            {'code': 'GOX', 'name': 'Manohar International Airport Mopa', 'city': 'Goa', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'PNQ', 'name': 'Pune International Airport', 'city': 'Pune', 'country': 'India', 'terminal': 'New Integrated Terminal'},
            {'code': 'AMD', 'name': 'Sardar Vallabhbhai Patel International', 'city': 'Ahmedabad', 'country': 'India', 'terminal': 'Terminal 1 & 2'},
            {'code': 'JAI', 'name': 'Jaipur International Airport', 'city': 'Jaipur', 'country': 'India', 'terminal': 'Terminal 2'},
            {'code': 'COK', 'name': 'Cochin International Airport', 'city': 'Kochi', 'country': 'India', 'terminal': 'Terminal 3'},
            {'code': 'TRV', 'name': 'Thiruvananthapuram International Airport', 'city': 'Thiruvananthapuram', 'country': 'India', 'terminal': 'Terminal 2'},
            {'code': 'CCJ', 'name': 'Calicut International Airport', 'city': 'Kozhikode', 'country': 'India', 'terminal': 'Terminal 1'},
            {'code': 'IXC', 'name': 'Shaheed Bhagat Singh International Airport', 'city': 'Chandigarh', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'ATQ', 'name': 'Sri Guru Ram Dass Jee International Airport', 'city': 'Amritsar', 'country': 'India', 'terminal': 'Terminal 1'},
            {'code': 'SXR', 'name': 'Sheikh ul-Alam International Airport', 'city': 'Srinagar', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'IXJ', 'name': 'Jammu Domestic Airport', 'city': 'Jammu', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'DED', 'name': 'Jolly Grant Airport', 'city': 'Dehradun', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'GAU', 'name': 'Lokpriya Gopinath Bordoloi International', 'city': 'Guwahati', 'country': 'India', 'terminal': 'Terminal 1'},
            {'code': 'BBI', 'name': 'Biju Patnaik International Airport', 'city': 'Bhubaneswar', 'country': 'India', 'terminal': 'Terminal 1'},
            {'code': 'PAT', 'name': 'Jay Prakash Narayan Airport', 'city': 'Patna', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'LKO', 'name': 'Chaudhary Charan Singh International', 'city': 'Lucknow', 'country': 'India', 'terminal': 'Terminal 3'},
            {'code': 'VNS', 'name': 'Lal Bahadur Shastri International', 'city': 'Varanasi', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'AYJ', 'name': 'Maharishi Valmiki International Airport', 'city': 'Ayodhya', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'IDR', 'name': 'Devi Ahilyabai Holkar Airport', 'city': 'Indore', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'BHO', 'name': 'Raja Bhoj Airport', 'city': 'Bhopal', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'NAG', 'name': 'Dr. Babasaheb Ambedkar International', 'city': 'Nagpur', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'STV', 'name': 'Surat International Airport', 'city': 'Surat', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'BDQ', 'name': 'Vadodara Airport', 'city': 'Vadodara', 'country': 'India', 'terminal': 'Integrated Terminal'},
            {'code': 'UDR', 'name': 'Maharana Pratap Airport', 'city': 'Udaipur', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'JDH', 'name': 'Jodhpur Airport', 'city': 'Jodhpur', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'VTZ', 'name': 'Visakhapatnam Airport', 'city': 'Visakhapatnam', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'TIR', 'name': 'Tirupati International Airport', 'city': 'Tirupati', 'country': 'India', 'terminal': 'Garuda Terminal'},
            {'code': 'CJB', 'name': 'Coimbatore International Airport', 'city': 'Coimbatore', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'MYS', 'name': 'Mysore Airport', 'city': 'Mysuru', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'IXE', 'name': 'Mangaluru International Airport', 'city': 'Mangaluru', 'country': 'India', 'terminal': 'Integrated Terminal'},
            {'code': 'IXR', 'name': 'Birsa Munda Airport', 'city': 'Ranchi', 'country': 'India', 'terminal': 'Main Terminal'},
            {'code': 'RPR', 'name': 'Swami Vivekananda Airport', 'city': 'Raipur', 'country': 'India', 'terminal': 'Domestic Terminal'},
            {'code': 'DXB', 'name': 'Dubai International Airport', 'city': 'Dubai', 'country': 'UAE', 'terminal': 'Terminal 3'},
            {'code': 'SIN', 'name': 'Singapore Changi Airport', 'city': 'Singapore', 'country': 'Singapore', 'terminal': 'Terminal 1'},
            {'code': 'BKK', 'name': 'Suvarnabhumi International Airport', 'city': 'Bangkok', 'country': 'Thailand', 'terminal': 'Main Terminal'},
        ]

        airports_dict = {}
        for a in airports_data:
            apt, _ = Airport.objects.get_or_create(code=a['code'], defaults=a)
            airports_dict[a['code']] = apt

        airlines_data = [
            {'code': 'AI', 'name': 'Air India', 'logo_icon': 'fa-plane-departure', 'callsign': 'AIRINDIA'},
            {'code': '6E', 'name': 'IndiGo Airlines', 'logo_icon': 'fa-plane-tail', 'callsign': 'IFLY'},
            {'code': 'UK', 'name': 'Vistara', 'logo_icon': 'fa-paper-plane', 'callsign': 'VISTARA'},
            {'code': 'SG', 'name': 'SpiceJet', 'logo_icon': 'fa-fighter-jet', 'callsign': 'SPICEJET'},
            {'code': 'QP', 'name': 'Akasa Air', 'logo_icon': 'fa-plane', 'callsign': 'AKASA'},
        ]

        airlines_dict = {}
        for al in airlines_data:
            airl, _ = Airline.objects.get_or_create(code=al['code'], defaults=al)
            airlines_dict[al['code']] = airl

        aircraft_data = [
            {'model_name': 'Airbus A321neo', 'total_capacity': 220},
            {'model_name': 'Boeing 787-9 Dreamliner', 'total_capacity': 290},
            {'model_name': 'Boeing 737 MAX 8', 'total_capacity': 189},
            {'model_name': 'Airbus A320neo', 'total_capacity': 186},
        ]

        aircraft_objs = []
        for ac in aircraft_data:
            ac_obj, _ = Aircraft.objects.get_or_create(model_name=ac['model_name'], defaults=ac)
            aircraft_objs.append(ac_obj)

        flights_data = [
            {'flight_number': 'AI-805', 'airline': 'AI', 'aircraft': aircraft_objs[1]},
            {'flight_number': 'AI-806', 'airline': 'AI', 'aircraft': aircraft_objs[1]},
            {'flight_number': '6E-2041', 'airline': '6E', 'aircraft': aircraft_objs[3]},
            {'flight_number': '6E-5012', 'airline': '6E', 'aircraft': aircraft_objs[3]},
            {'flight_number': 'UK-993', 'airline': 'UK', 'aircraft': aircraft_objs[0]},
            {'flight_number': 'UK-996', 'airline': 'UK', 'aircraft': aircraft_objs[0]},
            {'flight_number': 'AI-540', 'airline': 'AI', 'aircraft': aircraft_objs[0]},
            {'flight_number': 'UK-848', 'airline': 'UK', 'aircraft': aircraft_objs[0]},
            {'flight_number': 'QP-1322', 'airline': 'QP', 'aircraft': aircraft_objs[2]},
            {'flight_number': 'QP-1102', 'airline': 'QP', 'aircraft': aircraft_objs[2]},
            {'flight_number': '6E-334', 'airline': '6E', 'aircraft': aircraft_objs[3]},
            {'flight_number': 'AI-624', 'airline': 'AI', 'aircraft': aircraft_objs[0]},
            {'flight_number': '6E-789', 'airline': '6E', 'aircraft': aircraft_objs[3]},
            {'flight_number': 'AI-214', 'airline': 'AI', 'aircraft': aircraft_objs[1]},
            {'flight_number': 'AI-215', 'airline': 'AI', 'aircraft': aircraft_objs[1]},
        ]

        flights_dict = {}
        for f in flights_data:
            fl_obj, _ = Flight.objects.get_or_create(
                flight_number=f['flight_number'],
                defaults={'airline': airlines_dict[f['airline']], 'aircraft': f['aircraft']}
            )
            flights_dict[f['flight_number']] = fl_obj

        flight_schedule_specs = [
            # Mumbai (BOM) -> New Delhi (DEL) - Multiple daily flights
            {
                'flight': 'AI-806', 'orig': 'BOM', 'dest': 'DEL', 'dep_hour': 6, 'dep_min': 30, 'dur': 130, 'stops': 0,
                'eco': Decimal('4600.00'), 'prem': Decimal('6900.00'), 'biz': Decimal('15500.00'), 'fst': Decimal('27500.00')
            },
            {
                'flight': 'UK-996', 'orig': 'BOM', 'dest': 'DEL', 'dep_hour': 14, 'dep_min': 15, 'dur': 135, 'stops': 0,
                'eco': Decimal('4900.00'), 'prem': Decimal('7300.00'), 'biz': Decimal('16200.00'), 'fst': Decimal('28500.00')
            },
            {
                'flight': '6E-5012', 'orig': 'BOM', 'dest': 'DEL', 'dep_hour': 18, 'dep_min': 45, 'dur': 130, 'stops': 0,
                'eco': Decimal('4400.00'), 'prem': Decimal('6500.00'), 'biz': Decimal('14500.00'), 'fst': Decimal('25000.00')
            },
            {
                'flight': 'QP-1102', 'orig': 'BOM', 'dest': 'DEL', 'dep_hour': 21, 'dep_min': 0, 'dur': 130, 'stops': 0,
                'eco': Decimal('3900.00'), 'prem': Decimal('5900.00'), 'biz': Decimal('12900.00'), 'fst': Decimal('22500.00')
            },

            # New Delhi (DEL) -> Mumbai (BOM)
            {
                'flight': 'AI-805', 'orig': 'DEL', 'dest': 'BOM', 'dep_hour': 7, 'dep_min': 0, 'dur': 130, 'stops': 0,
                'eco': Decimal('4800.00'), 'prem': Decimal('7200.00'), 'biz': Decimal('16500.00'), 'fst': Decimal('29000.00')
            },
            {
                'flight': '6E-2041', 'orig': 'DEL', 'dest': 'BOM', 'dep_hour': 10, 'dep_min': 30, 'dur': 135, 'stops': 0,
                'eco': Decimal('4100.00'), 'prem': Decimal('6200.00'), 'biz': Decimal('13500.00'), 'fst': Decimal('24000.00')
            },

            # Delhi <-> Bengaluru
            {
                'flight': 'UK-993', 'orig': 'DEL', 'dest': 'BLR', 'dep_hour': 8, 'dep_min': 15, 'dur': 165, 'stops': 0,
                'eco': Decimal('5400.00'), 'prem': Decimal('8100.00'), 'biz': Decimal('18200.00'), 'fst': Decimal('32000.00')
            },
            {
                'flight': 'AI-540', 'orig': 'BLR', 'dest': 'DEL', 'dep_hour': 16, 'dep_min': 0, 'dur': 160, 'stops': 0,
                'eco': Decimal('5200.00'), 'prem': Decimal('7900.00'), 'biz': Decimal('17500.00'), 'fst': Decimal('31000.00')
            },

            # Delhi / Mumbai <-> Goa
            {
                'flight': 'UK-848', 'orig': 'DEL', 'dest': 'GOI', 'dep_hour': 11, 'dep_min': 20, 'dur': 155, 'stops': 0,
                'eco': Decimal('5900.00'), 'prem': Decimal('8900.00'), 'biz': Decimal('19800.00'), 'fst': Decimal('34000.00')
            },
            {
                'flight': '6E-334', 'orig': 'GOI', 'dest': 'DEL', 'dep_hour': 15, 'dep_min': 40, 'dur': 150, 'stops': 0,
                'eco': Decimal('5800.00'), 'prem': Decimal('8600.00'), 'biz': Decimal('19200.00'), 'fst': Decimal('33000.00')
            },
            {
                'flight': 'AI-624', 'orig': 'BOM', 'dest': 'GOI', 'dep_hour': 9, 'dep_min': 0, 'dur': 75, 'stops': 0,
                'eco': Decimal('3200.00'), 'prem': Decimal('4800.00'), 'biz': Decimal('10500.00'), 'fst': Decimal('19000.00')
            },
            {
                'flight': '6E-789', 'orig': 'GOI', 'dest': 'BOM', 'dep_hour': 18, 'dep_min': 0, 'dur': 75, 'stops': 0,
                'eco': Decimal('3300.00'), 'prem': Decimal('4900.00'), 'biz': Decimal('10800.00'), 'fst': Decimal('19500.00')
            },

            # Mumbai <-> Bengaluru
            {
                'flight': 'QP-1322', 'orig': 'BOM', 'dest': 'BLR', 'dep_hour': 14, 'dep_min': 10, 'dur': 105, 'stops': 0,
                'eco': Decimal('3600.00'), 'prem': Decimal('5400.00'), 'biz': Decimal('11500.00'), 'fst': Decimal('21000.00')
            },

            # International: Delhi <-> Dubai
            {
                'flight': 'AI-214', 'orig': 'DEL', 'dest': 'DXB', 'dep_hour': 13, 'dep_min': 0, 'dur': 225, 'stops': 0,
                'eco': Decimal('12500.00'), 'prem': Decimal('18500.00'), 'biz': Decimal('38000.00'), 'fst': Decimal('65000.00')
            },
            {
                'flight': 'AI-215', 'orig': 'DXB', 'dest': 'DEL', 'dep_hour': 18, 'dep_min': 30, 'dur': 210, 'stops': 0,
                'eco': Decimal('12800.00'), 'prem': Decimal('18900.00'), 'biz': Decimal('39000.00'), 'fst': Decimal('66000.00')
            },
        ]

        for day_offset in range(-3, 36):
            curr_date = today + timedelta(days=day_offset)
            for spec in flight_schedule_specs:
                dep_dt = datetime.combine(curr_date, time(spec['dep_hour'], spec['dep_min']))
                dep_dt = timezone.make_aware(dep_dt, timezone.get_current_timezone())
                arr_dt = dep_dt + timedelta(minutes=spec['dur'])

                fl_sched, fl_created = FlightSchedule.objects.get_or_create(
                    flight=flights_dict[spec['flight']],
                    origin_airport=airports_dict[spec['orig']],
                    destination_airport=airports_dict[spec['dest']],
                    departure_datetime=dep_dt,
                    defaults={
                        'arrival_datetime': arr_dt,
                        'duration_minutes': spec['dur'],
                        'stops': spec['stops'],
                        'fare_economy': spec['eco'],
                        'fare_premium_economy': spec['prem'],
                        'fare_business': spec['biz'],
                        'fare_first_class': spec['fst'],
                    }
                )

                if fl_created or fl_sched.seats.count() == 0:
                    flight_seats = []
                    # 1. First Class Suites (Rows 1-2, Cols A, B, E, F)
                    for r in [1, 2]:
                        for c in ['A', 'B', 'E', 'F']:
                            st = 'WINDOW' if c in ['A', 'F'] else 'AISLE'
                            flight_seats.append(FlightSeat(
                                schedule=fl_sched,
                                seat_number=f"{r}{c}",
                                row_number=r,
                                column_letter=c,
                                cabin_class='FIRST_CLASS',
                                seat_type=st,
                                is_booked=(r == 1 and c == 'B')
                            ))

                    # 2. Business Class (Rows 3-5, Cols A, C, D, F)
                    for r in range(3, 6):
                        for c in ['A', 'C', 'D', 'F']:
                            st = 'WINDOW' if c in ['A', 'F'] else 'AISLE'
                            flight_seats.append(FlightSeat(
                                schedule=fl_sched,
                                seat_number=f"{r}{c}",
                                row_number=r,
                                column_letter=c,
                                cabin_class='BUSINESS',
                                seat_type=st,
                                is_booked=(r == 3 and c == 'A')
                            ))

                    # 3. Premium Economy (Rows 6-9, Cols A, B, C, D, E, F)
                    for r in range(6, 10):
                        for c in ['A', 'B', 'C', 'D', 'E', 'F']:
                            st = 'EXTRA_LEGROOM' if c in ['A', 'F'] else ('AISLE' if c in ['C', 'D'] else 'MIDDLE')
                            flight_seats.append(FlightSeat(
                                schedule=fl_sched,
                                seat_number=f"{r}{c}",
                                row_number=r,
                                column_letter=c,
                                cabin_class='PREMIUM_ECONOMY',
                                seat_type=st,
                                is_booked=(r == 7 and c == 'C')
                            ))

                    # 4. Economy Class (Rows 10-25, Cols A, B, C, D, E, F)
                    for r in range(10, 26):
                        for c in ['A', 'B', 'C', 'D', 'E', 'F']:
                            st = 'WINDOW' if c in ['A', 'F'] else ('AISLE' if c in ['C', 'D'] else 'MIDDLE')
                            flight_seats.append(FlightSeat(
                                schedule=fl_sched,
                                seat_number=f"{r}{c}",
                                row_number=r,
                                column_letter=c,
                                cabin_class='ECONOMY',
                                seat_type=st,
                                is_booked=(r in [12, 18] and c in ['A', 'F'])
                            ))

                    FlightSeat.objects.bulk_create(flight_seats, ignore_conflicts=True)

        # ==========================================
        # 4. BUSES SEEDING
        # ==========================================
        self.stdout.write("Seeding Bus operators, buses, routes, schedules & decks...")

        operators_data = [
            {'name': 'Zingbus Smart Bus', 'contact_number': '+91 1800-102-8899', 'rating': Decimal('4.8')},
            {'name': 'IntrCity SmartBus', 'contact_number': '+91 1800-120-7766', 'rating': Decimal('4.7')},
            {'name': 'KSRTC (Airavat Club Class)', 'contact_number': '+91 80-2222-1314', 'rating': Decimal('4.6')},
            {'name': 'SRS Travels', 'contact_number': '+91 80-2680-9999', 'rating': Decimal('4.4')},
            {'name': 'Orange Travels', 'contact_number': '+91 1800-200-5544', 'rating': Decimal('4.5')},
            {'name': 'VRL Travels', 'contact_number': '+91 1800-425-4555', 'rating': Decimal('4.6')},
        ]

        operators_dict = {}
        for op in operators_data:
            op_obj, _ = BusOperator.objects.get_or_create(name=op['name'], defaults=op)
            operators_dict[op['name']] = op_obj

        buses_data = [
            {'bus_number': 'DL-01-ZB-2024', 'operator': 'Zingbus Smart Bus', 'bus_type': 'VOLVO', 'total_seats': 36, 'has_sleeper': True},
            {'bus_number': 'HR-55-IC-9812', 'operator': 'IntrCity SmartBus', 'bus_type': 'AC_SLEEPER', 'total_seats': 30, 'has_sleeper': True},
            {'bus_number': 'KA-01-F-7744', 'operator': 'KSRTC (Airavat Club Class)', 'bus_type': 'VOLVO', 'total_seats': 44, 'has_sleeper': False},
            {'bus_number': 'MH-12-SRS-502', 'operator': 'SRS Travels', 'bus_type': 'SEMI_SLEEPER', 'total_seats': 40, 'has_sleeper': False},
            {'bus_number': 'TS-09-OT-8821', 'operator': 'Orange Travels', 'bus_type': 'AC_SLEEPER', 'total_seats': 32, 'has_sleeper': True},
            {'bus_number': 'KA-25-VRL-1102', 'operator': 'VRL Travels', 'bus_type': 'VOLVO', 'total_seats': 38, 'has_sleeper': True},
        ]

        buses_dict = {}
        for b in buses_data:
            b_obj, _ = Bus.objects.get_or_create(
                bus_number=b['bus_number'],
                defaults={
                    'operator': operators_dict[b['operator']],
                    'bus_type': b['bus_type'],
                    'total_seats': b['total_seats'],
                    'has_sleeper': b['has_sleeper'],
                }
            )
            buses_dict[b['bus_number']] = b_obj

        routes_data = [
            {
                'src': 'New Delhi', 'dst': 'Agra', 'dist': 230,
                'bp': 'Sarai Kale Khan ISBT, Yamuna Expressway, Akshardham',
                'dp': 'Idgah Bus Stand Agra, Fatehabad Road, Water Works'
            },
            {
                'src': 'Agra', 'dst': 'New Delhi', 'dist': 230,
                'bp': 'Water Works Agra, Idgah Bus Stand, Express Highway',
                'dp': 'Akshardham, Sarai Kale Khan ISBT, Kashmiri Gate'
            },
            {
                'src': 'New Delhi', 'dst': 'Chandigarh', 'dist': 250,
                'bp': 'Kashmere Gate ISBT, Majnu Ka Tilla, Singhu Border',
                'dp': 'Sector 43 ISBT, Tribune Chowk, Sector 17'
            },
            {
                'src': 'Chandigarh', 'dst': 'New Delhi', 'dist': 250,
                'bp': 'Sector 43 ISBT, Tribune Chowk, Mohali Phase 7',
                'dp': 'Singhu Border, Majnu Ka Tilla, Kashmere Gate ISBT'
            },
            {
                'src': 'New Delhi', 'dst': 'Rishikesh', 'dist': 240,
                'bp': 'Kashmiri Gate ISBT, Anand Vihar ISBT, Mohan Nagar',
                'dp': 'Nepali Farm, Natraj Chowk, Tapovan Rishikesh'
            },
            {
                'src': 'Rishikesh', 'dst': 'New Delhi', 'dist': 240,
                'bp': 'Tapovan, Natraj Chowk, Nepali Farm, Haridwar Bypass',
                'dp': 'Anand Vihar ISBT, Kashmiri Gate ISBT'
            },
            {
                'src': 'New Delhi', 'dst': 'Shimla', 'dist': 340,
                'bp': 'Majnu Ka Tilla, Kashmiri Gate ISBT, Karnal Bypass',
                'dp': 'ISBT Tutikandi Shimla, Victory Tunnel, Old Bus Stand'
            },
            {
                'src': 'Shimla', 'dst': 'New Delhi', 'dist': 340,
                'bp': 'ISBT Tutikandi Shimla, Shoghi, Kandaghat',
                'dp': 'Karnal Bypass, Kashmiri Gate ISBT, Majnu Ka Tilla'
            },
            {
                'src': 'Mumbai', 'dst': 'Ahmedabad', 'dist': 525,
                'bp': 'Borivali West, Malad East, Andheri, Vapi Toll, Surat Bypass',
                'dp': 'Geeta Mandir Bus Stand, Paldi, CTM Cross Road, Iscon'
            },
            {
                'src': 'Ahmedabad', 'dst': 'Mumbai', 'dist': 525,
                'bp': 'Paldi, Iscon Cross Road, CTM, Geeta Mandir',
                'dp': 'Dahisar, Borivali, Andheri, Dadar TT'
            },
            {
                'src': 'Pune', 'dst': 'Goa', 'dist': 450,
                'bp': 'Swargate, Pune Station, Katraj Bypass, Chandani Chowk',
                'dp': 'Mapusa, Panjim KTC Bus Stand, Madgaon'
            },
            {
                'src': 'Goa', 'dst': 'Pune', 'dist': 450,
                'bp': 'Madgaon, Panjim KTC, Mapusa, Banda',
                'dp': 'Katraj Bypass, Swargate, Pune Station'
            },
            {
                'src': 'Jaipur', 'dst': 'Udaipur', 'dist': 390,
                'bp': 'Sindhi Camp, 200 Ft Bypass, Gopalpura Flyover',
                'dp': 'Udaipole, Reti Stand, Sukher Bypass'
            },
            {
                'src': 'Udaipur', 'dst': 'Jaipur', 'dist': 390,
                'bp': 'Udaipole, Reti Stand, Bhuwana Bypass',
                'dp': '200 Ft Bypass, Sindhi Camp, Gopalpura'
            },
            {
                'src': 'Lucknow', 'dst': 'Varanasi', 'dist': 310,
                'bp': 'Alambagh ISBT, Charbagh, Gomti Nagar Bypass',
                'dp': 'Cantt Bus Stand Varanasi, Lahartara, Lanka'
            },
            {
                'src': 'Varanasi', 'dst': 'Lucknow', 'dist': 310,
                'bp': 'Cantt Bus Stand Varanasi, Lahartara, Babatpur',
                'dp': 'Gomti Nagar Bypass, Charbagh, Alambagh ISBT'
            },
            {
                'src': 'Lucknow', 'dst': 'Ayodhya', 'dist': 135,
                'bp': 'Alambagh, Polytechnic Crossing, Kamta Bus Stand',
                'dp': 'Ayodhya Dham Bus Stand, Ram Ki Paidi, Naya Ghat'
            },
            {
                'src': 'Ayodhya', 'dst': 'Lucknow', 'dist': 135,
                'bp': 'Ayodhya Dham Bus Stand, Naya Ghat, Bypass',
                'dp': 'Kamta Bus Stand, Polytechnic, Alambagh'
            },
            {
                'src': 'Bengaluru', 'dst': 'Goa', 'dist': 560,
                'bp': 'Majestic, Yeshwantpur, Goraguntepalya, Tumkur Bypass',
                'dp': 'Madgaon, Panaji, Mapusa'
            },
            {
                'src': 'Goa', 'dst': 'Bengaluru', 'dist': 560,
                'bp': 'Mapusa, Panaji, Madgaon, Ponda',
                'dp': 'Tumkur Bypass, Goraguntepalya, Yeshwantpur, Majestic'
            },
            {
                'src': 'Bengaluru', 'dst': 'Kochi', 'dist': 540,
                'bp': 'Majestic, Shantinagar, Madiwala, Electronic City',
                'dp': 'Aluva, Edappally, Vyttila Mobility Hub, Ernakulam'
            },
            {
                'src': 'Kochi', 'dst': 'Bengaluru', 'dist': 540,
                'bp': 'Vyttila Mobility Hub, Edappally, Aluva, Angamaly',
                'dp': 'Electronic City, Madiwala, Shantinagar, Majestic'
            },
            {
                'src': 'Chennai', 'dst': 'Coimbatore', 'dist': 510,
                'bp': 'Koyambedu CMBT, Ashok Nagar, Guindy, Tambaram',
                'dp': 'Gandhipuram, Hopes College, Singanallur'
            },
            {
                'src': 'Coimbatore', 'dst': 'Chennai', 'dist': 510,
                'bp': 'Gandhipuram, Omni Bus Stand, Hopes College, KMCH',
                'dp': 'Tambaram, Guindy, Ashok Nagar, Koyambedu CMBT'
            },
            {
                'src': 'Hyderabad', 'dst': 'Vijayawada', 'dist': 275,
                'bp': 'MGBS, LB Nagar, Dilsukhnagar, Uppal',
                'dp': 'Pandit Nehru Bus Station, Benz Circle, RTC Complex'
            },
            {
                'src': 'Vijayawada', 'dst': 'Hyderabad', 'dist': 275,
                'bp': 'Pandit Nehru Bus Station, Benz Circle, Gollapudi',
                'dp': 'LB Nagar, Dilsukhnagar, MGBS, Lakdikapul'
            },
        ]

        routes_dict = {}
        for r in routes_data:
            r_obj, _ = BusRoute.objects.get_or_create(
                source_city=r['src'], destination_city=r['dst'],
                defaults={
                    'boarding_points': r['bp'],
                    'dropping_points': r['dp'],
                    'distance_km': r['dist']
                }
            )
            routes_dict[f"{r['src']}->{r['dst']}"] = r_obj

        bus_schedules_specs = [
            {'bus': 'DL-01-ZB-2024', 'route': 'New Delhi->Jaipur', 'dep': time(6, 30), 'arr': time(11, 30), 'dur': 300, 'fare': Decimal('650.00')},
            {'bus': 'DL-01-ZB-2024', 'route': 'Jaipur->New Delhi', 'dep': time(16, 30), 'arr': time(21, 30), 'dur': 300, 'fare': Decimal('650.00')},
            {'bus': 'HR-55-IC-9812', 'route': 'New Delhi->Manali', 'dep': time(18, 0), 'arr': time(8, 0), 'dur': 840, 'fare': Decimal('1450.00')},
            {'bus': 'HR-55-IC-9812', 'route': 'Manali->New Delhi', 'dep': time(18, 30), 'arr': time(8, 30), 'dur': 840, 'fare': Decimal('1450.00')},
            {'bus': 'MH-12-SRS-502', 'route': 'Mumbai->Pune', 'dep': time(7, 0), 'arr': time(10, 30), 'dur': 210, 'fare': Decimal('380.00')},
            {'bus': 'MH-12-SRS-502', 'route': 'Pune->Mumbai', 'dep': time(17, 0), 'arr': time(20, 30), 'dur': 210, 'fare': Decimal('380.00')},
            {'bus': 'DL-01-ZB-2024', 'route': 'Mumbai->Goa', 'dep': time(17, 30), 'arr': time(7, 30), 'dur': 840, 'fare': Decimal('1650.00')},
            {'bus': 'DL-01-ZB-2024', 'route': 'Goa->Mumbai', 'dep': time(18, 0), 'arr': time(8, 0), 'dur': 840, 'fare': Decimal('1650.00')},
            {'bus': 'KA-01-F-7744', 'route': 'Bengaluru->Chennai', 'dep': time(23, 0), 'arr': time(5, 30), 'dur': 390, 'fare': Decimal('890.00')},
            {'bus': 'KA-01-F-7744', 'route': 'Chennai->Bengaluru', 'dep': time(22, 30), 'arr': time(5, 0), 'dur': 390, 'fare': Decimal('890.00')},
            {'bus': 'TS-09-OT-8821', 'route': 'Bengaluru->Hyderabad', 'dep': time(21, 30), 'arr': time(6, 30), 'dur': 540, 'fare': Decimal('1250.00')},
            {'bus': 'TS-09-OT-8821', 'route': 'Hyderabad->Bengaluru', 'dep': time(21, 0), 'arr': time(6, 0), 'dur': 540, 'fare': Decimal('1250.00')},
        ]

        for day_offset in range(-3, 36):
            curr_date = today + timedelta(days=day_offset)
            for spec in bus_schedules_specs:
                if spec['route'] not in routes_dict:
                    continue
                bs_obj, bs_created = BusSchedule.objects.get_or_create(
                    bus=buses_dict[spec['bus']],
                    route=routes_dict[spec['route']],
                    journey_date=curr_date,
                    defaults={
                        'departure_time': spec['dep'],
                        'arrival_time': spec['arr'],
                        'duration_minutes': spec['dur'],
                        'base_fare': spec['fare'],
                    }
                )

                if bs_created or bs_obj.seats.count() == 0:
                    bus_seats = []
                    # Lower deck
                    for s in range(1, 19):
                        bus_seats.append(BusSeat(
                            schedule=bs_obj,
                            seat_number=f"L{s}",
                            deck='LOWER',
                            seat_type='SEATER' if s <= 10 else 'SLEEPER',
                            is_ladies_only=(s in [1, 2]),
                            is_booked=(s in [3, 7])
                        ))
                    # Upper deck
                    for s in range(1, 13):
                        bus_seats.append(BusSeat(
                            schedule=bs_obj,
                            seat_number=f"U{s}",
                            deck='UPPER',
                            seat_type='SLEEPER',
                            is_ladies_only=False,
                            is_booked=(s in [1, 5])
                        ))
                    BusSeat.objects.bulk_create(bus_seats, ignore_conflicts=True)

        # ==========================================
        # 5. SAMPLE REALISTIC BOOKINGS & PAYMENTS
        # ==========================================
        self.stdout.write("Creating sample customer bookings & confirmed payments...")

        # Booking 1: Confirmed Train Booking for Rohan
        train_sched_sample = TrainSchedule.objects.filter(journey_date__gte=today).first()
        if train_sched_sample:
            booking1, b1_created = Booking.objects.get_or_create(
                pnr=f"RAW-{today.year}-8F73K2",
                defaults={
                    'user': customer_user,
                    'transport_type': 'TRAIN',
                    'train_schedule': train_sched_sample,
                    'service_title': f"{train_sched_sample.train.name} ({train_sched_sample.train.train_number})",
                    'travel_class': 'AC_3_TIER',
                    'source_location': f"{train_sched_sample.source_station.name} ({train_sched_sample.source_station.code})",
                    'destination_location': f"{train_sched_sample.destination_station.name} ({train_sched_sample.destination_station.code})",
                    'journey_date': train_sched_sample.journey_date,
                    'departure_time': train_sched_sample.departure_time.strftime('%H:%M'),
                    'arrival_time': train_sched_sample.arrival_time.strftime('%H:%M'),
                    'duration_text': train_sched_sample.formatted_duration,
                    'passenger_count': 2,
                    'allocated_seats': 'B1-12, B1-13',
                    'base_fare': Decimal('2500.00'),
                    'taxes': Decimal('125.00'),
                    'service_fee': Decimal('49.00'),
                    'discount': Decimal('100.00'),
                    'total_amount': Decimal('2574.00'),
                    'booking_status': 'CONFIRMED',
                    'payment_status': 'SUCCESS',
                }
            )
            if b1_created:
                Passenger.objects.create(
                    booking=booking1, full_name='Rohan Sharma', age=29, gender='MALE',
                    phone='+91 9811223344', email='customer@railaway.com',
                    id_type='AADHAAR', id_number='541298761234', seat_number='B1-12', berth_preference='LOWER'
                )
                Passenger.objects.create(
                    booking=booking1, full_name='Pooja Sharma', age=27, gender='FEMALE',
                    phone='+91 9811223344', email='customer@railaway.com',
                    id_type='AADHAAR', id_number='984512347612', seat_number='B1-13', berth_preference='UPPER'
                )
                Payment.objects.create(
                    booking=booking1, transaction_id=f"TXN-{today.year}-98412034",
                    payment_method='CREDIT_CARD', amount=Decimal('2574.00'),
                    payment_status='SUCCESS', card_last4='4242', card_network='Visa'
                )

        # Booking 2: Confirmed Flight Booking for Rohan
        flight_sched_sample = FlightSchedule.objects.filter(departure_datetime__date__gte=today).first()
        if flight_sched_sample:
            booking2, b2_created = Booking.objects.get_or_create(
                pnr=f"RAW-{today.year}-99XK14",
                defaults={
                    'user': customer_user,
                    'transport_type': 'FLIGHT',
                    'flight_schedule': flight_sched_sample,
                    'service_title': f"{flight_sched_sample.flight.airline.name} {flight_sched_sample.flight.flight_number}",
                    'travel_class': 'ECONOMY',
                    'source_location': f"{flight_sched_sample.origin_airport.name} ({flight_sched_sample.origin_airport.code})",
                    'destination_location': f"{flight_sched_sample.destination_airport.name} ({flight_sched_sample.destination_airport.code})",
                    'journey_date': flight_sched_sample.departure_datetime.date(),
                    'departure_time': flight_sched_sample.departure_datetime.strftime('%H:%M'),
                    'arrival_time': flight_sched_sample.arrival_datetime.strftime('%H:%M'),
                    'duration_text': flight_sched_sample.formatted_duration,
                    'passenger_count': 1,
                    'allocated_seats': '14A',
                    'base_fare': flight_sched_sample.fare_economy,
                    'taxes': Decimal('576.00'),
                    'service_fee': Decimal('49.00'),
                    'discount': Decimal('0.00'),
                    'total_amount': flight_sched_sample.fare_economy + Decimal('625.00'),
                    'booking_status': 'CONFIRMED',
                    'payment_status': 'SUCCESS',
                }
            )
            if b2_created:
                Passenger.objects.create(
                    booking=booking2, full_name='Rohan Sharma', age=29, gender='MALE',
                    phone='+91 9811223344', email='customer@railaway.com',
                    id_type='PASSPORT', id_number='Z1984271', seat_number='14A'
                )
                Payment.objects.create(
                    booking=booking2, transaction_id=f"TXN-{today.year}-33219012",
                    payment_method='UPI', amount=booking2.total_amount,
                    payment_status='SUCCESS', upi_id='rohan@okaxis'
                )

        # Booking 3: Cancelled Bus Booking to test cancellation/refund view
        bus_sched_sample = BusSchedule.objects.filter(journey_date__gte=today).first()
        if bus_sched_sample:
            booking3, b3_created = Booking.objects.get_or_create(
                pnr=f"RAW-{today.year}-5T7B99",
                defaults={
                    'user': customer_user,
                    'transport_type': 'BUS',
                    'bus_schedule': bus_sched_sample,
                    'service_title': f"{bus_sched_sample.bus.operator.name} ({bus_sched_sample.bus.bus_number})",
                    'travel_class': 'VOLVO',
                    'source_location': bus_sched_sample.route.source_city,
                    'destination_location': bus_sched_sample.route.destination_city,
                    'journey_date': bus_sched_sample.journey_date,
                    'departure_time': bus_sched_sample.departure_time.strftime('%H:%M'),
                    'arrival_time': bus_sched_sample.arrival_time.strftime('%H:%M'),
                    'duration_text': bus_sched_sample.formatted_duration,
                    'passenger_count': 1,
                    'allocated_seats': 'L5',
                    'base_fare': Decimal('850.00'),
                    'taxes': Decimal('42.50'),
                    'service_fee': Decimal('49.00'),
                    'discount': Decimal('0.00'),
                    'total_amount': Decimal('941.50'),
                    'booking_status': 'CANCELLED',
                    'payment_status': 'REFUNDED',
                    'cancellation_reason': 'Plan postponed due to emergency meeting',
                    'cancelled_at': timezone.now() - timedelta(hours=5),
                    'refund_amount': Decimal('765.00'),
                }
            )
            if b3_created:
                Passenger.objects.create(
                    booking=booking3, full_name='Rohan Sharma', age=29, gender='MALE',
                    phone='+91 9811223344', email='customer@railaway.com',
                    id_type='AADHAAR', id_number='541298761234', seat_number='L5'
                )
                Payment.objects.create(
                    booking=booking3, transaction_id=f"TXN-{today.year}-11029481",
                    payment_method='NET_BANKING', amount=Decimal('941.50'),
                    payment_status='REFUNDED', bank_name='HDFC Bank'
                )

        # ==========================================
        # 6. FOOD CATERING (E-CATERING IN TRAIN)
        # ==========================================
        self.stdout.write("Seeding Food Catering categories, restaurants & menu items...")

        cat_thali, _ = FoodCategory.objects.get_or_create(name='Royal Indian Thalis', defaults={'slug': 'thalis', 'icon': 'fa-utensils', 'display_order': 1})
        cat_biryani, _ = FoodCategory.objects.get_or_create(name='Biryani & Rice Bowls', defaults={'slug': 'biryani', 'icon': 'fa-bowl-rice', 'display_order': 2})
        cat_breakfast, _ = FoodCategory.objects.get_or_create(name='Breakfast & Snacks', defaults={'slug': 'breakfast', 'icon': 'fa-mug-hot', 'display_order': 3})
        cat_jain, _ = FoodCategory.objects.get_or_create(name='Pure Jain Specials', defaults={'slug': 'jain', 'icon': 'fa-seedling', 'display_order': 4})
        cat_fastfood, _ = FoodCategory.objects.get_or_create(name='Fast Food & Combos', defaults={'slug': 'fast-food', 'icon': 'fa-burger', 'display_order': 5})
        cat_beverages, _ = FoodCategory.objects.get_or_create(name='Beverages & Desserts', defaults={'slug': 'beverages', 'icon': 'fa-glass-water', 'display_order': 6})

        # Station Restaurants
        ndls_stn = stations_dict.get('NDLS') or RailwayStation.objects.first()
        bsb_stn = stations_dict.get('BSB') or ndls_stn
        bom_stn = stations_dict.get('BOM') or stations_dict.get('MMCT') or ndls_stn
        pune_stn = stations_dict.get('PUNE') or ndls_stn
        sbc_stn = stations_dict.get('SBC') or ndls_stn
        cnb_stn = stations_dict.get('CNB') or ndls_stn

        restaurants_data = [
            {'station': ndls_stn, 'name': 'IRCTC Executive Food Plaza (NDLS)', 'cuisine': 'North Indian, Deluxe Thalis, Street Chaat', 'rating': Decimal('4.9'), 'is_pure_veg': False, 'image_url': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&auto=format&fit=crop&q=80'},
            {'station': ndls_stn, 'name': 'Haldirams Express Platform 1', 'cuisine': 'Pure Veg Indian Sweets, Chole Bhature, Thalis', 'rating': Decimal('4.8'), 'is_pure_veg': True, 'image_url': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80'},
            {'station': cnb_stn, 'name': 'Kanpur Central Grand Rasoi', 'cuisine': 'Awadhi Biryani, Paneer Butter Masala, Parathas', 'rating': Decimal('4.7'), 'is_pure_veg': False, 'image_url': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80'},
            {'station': bsb_stn, 'name': 'Kashi Annapurna Pure Veg Bhojnalaya', 'cuisine': 'Pure Jain & Satvik Thali, Banarasi Kachori', 'rating': Decimal('4.9'), 'is_pure_veg': True, 'image_url': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80'},
            {'station': bom_stn, 'name': 'Mumbai Central Tiffin Express', 'cuisine': 'Pav Bhaji, South Indian, Veg Pulao, Maharaja Thali', 'rating': Decimal('4.8'), 'is_pure_veg': False, 'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80'},
            {'station': sbc_stn, 'name': 'Saravana Bhavan Express Bengaluru', 'cuisine': 'Masala Dosa, Idli Vada, Ghee Sambar Rice, Filter Coffee', 'rating': Decimal('4.8'), 'is_pure_veg': True, 'image_url': 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80'},
        ]

        created_restaurants = []
        for r_data in restaurants_data:
            r_obj, _ = StationRestaurant.objects.get_or_create(
                station=r_data['station'],
                name=r_data['name'],
                defaults=r_data
            )
            created_restaurants.append(r_obj)

        r_ndls = created_restaurants[0]
        r_haldiram = created_restaurants[1]

        # Food Dishes
        dishes_data = [
            # Thalis
            {'restaurant': r_ndls, 'category': cat_thali, 'name': 'Executive Maharaja Deluxe Thali', 'desc': 'Paneer butter masala, Dal makhani, Mix veg, Jeera rice, 3 butter rotis, Gulab jamun, Raita, Salad & Papad.', 'price': Decimal('249.00'), 'is_veg': True, 'is_jain': False, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80'},
            {'restaurant': r_ndls, 'category': cat_thali, 'name': 'Special Non-Veg Murgh Thali', 'desc': 'Butter chicken masala, Egg curry, Jeera rice, 3 butter rotis, Raita, Salad & Sweet.', 'price': Decimal('299.00'), 'is_veg': False, 'is_jain': False, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&auto=format&fit=crop&q=80'},
            {'restaurant': r_haldiram, 'category': cat_thali, 'name': 'Standard Homestyle Veg Thali', 'desc': 'Dal tadka, Aloo jeera, Steamed rice, 4 tawa chapattis, Pickle & Salad.', 'price': Decimal('149.00'), 'is_veg': True, 'is_jain': False, 'bestseller': False, 'img': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80'},
            
            # Biryani
            {'restaurant': r_ndls, 'category': cat_biryani, 'name': 'Hyderabadi Dum Chicken Biryani', 'desc': 'Fragrant long-grain basmati rice layered with spiced tender chicken, served with Mirchi ka Salan and creamy Raita.', 'price': Decimal('230.00'), 'is_veg': False, 'is_jain': False, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80'},
            {'restaurant': r_haldiram, 'category': cat_biryani, 'name': 'Royal Shahi Veg Biryani Bowl', 'desc': 'Garden fresh veggies and marinated paneer cubes cooked on dum with aromatic spices and saffron.', 'price': Decimal('180.00'), 'is_veg': True, 'is_jain': False, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=600&auto=format&fit=crop&q=80'},
            
            # Breakfast & Snacks
            {'restaurant': r_haldiram, 'category': cat_breakfast, 'name': 'Amritsari Chole Bhature (2 Pcs)', 'desc': 'Piping hot puffed bhaturas served with spicy pindi chole, pickle and onion salad.', 'price': Decimal('120.00'), 'is_veg': True, 'is_jain': False, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=600&auto=format&fit=crop&q=80'},
            {'restaurant': r_ndls, 'category': cat_breakfast, 'name': 'South Indian Masala Dosa Combo', 'desc': 'Crispy golden dosa stuffed with spiced potato masala, served with 2 Idlis, piping hot Sambar and Coconut Chutney.', 'price': Decimal('135.00'), 'is_veg': True, 'is_jain': False, 'bestseller': False, 'img': 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&auto=format&fit=crop&q=80'},
            {'restaurant': r_haldiram, 'category': cat_breakfast, 'name': 'Indori Poha with Sev & Jalebi', 'desc': 'Fluffy steamed poha tempered with mustard seeds and peanuts, topped with spicy ratlami sev and 2 hot jalebis.', 'price': Decimal('99.00'), 'is_veg': True, 'is_jain': False, 'bestseller': False, 'img': 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80'},
            
            # Pure Jain Specials
            {'restaurant': r_haldiram, 'category': cat_jain, 'name': 'Pure Jain Shahi Paneer Thali', 'desc': 'No onion, no garlic pure Jain preparation: Shahi paneer, Dal fry, Jeera rice, 3 chapattis, Salad & Sweet.', 'price': Decimal('220.00'), 'is_veg': True, 'is_jain': True, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80'},
            {'restaurant': r_ndls, 'category': cat_jain, 'name': 'Jain Special Khichdi & Kadhi Bowl', 'desc': 'Comforting moong dal khichdi served with Gujarati sweet-sour kadhi and roasted papad.', 'price': Decimal('130.00'), 'is_veg': True, 'is_jain': True, 'bestseller': False, 'img': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80'},

            # Beverages & Desserts
            {'restaurant': r_haldiram, 'category': cat_beverages, 'name': 'Kulhad Masala Chai (2 Cups)', 'desc': 'Brewed with cardamom, ginger, and fresh milk in authentic clay kulhad cups.', 'price': Decimal('49.00'), 'is_veg': True, 'is_jain': True, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80'},
            {'restaurant': r_haldiram, 'category': cat_beverages, 'name': 'Hot Gulab Jamun (2 Pcs)', 'desc': 'Soft melt-in-the-mouth mawa gulab jamuns dipped in rose-cardamom sugar syrup.', 'price': Decimal('60.00'), 'is_veg': True, 'is_jain': True, 'bestseller': True, 'img': 'https://images.unsplash.com/photo-1593701461250-d7b22dfd3a77?w=600&auto=format&fit=crop&q=80'},
        ]

        for d in dishes_data:
            FoodItem.objects.get_or_create(
                restaurant=d['restaurant'],
                name=d['name'],
                defaults={
                    'category': d['category'],
                    'description': d['desc'],
                    'price': d['price'],
                    'is_veg': d['is_veg'],
                    'is_jain': d['is_jain'],
                    'is_bestseller': d['bestseller'],
                    'image_url': d['img'],
                    'is_available': True,
                }
            )

        # Sample Food Order for Rohan
        food_order_sample, fo_created = FoodOrder.objects.get_or_create(
            order_ref=f"FOOD-{today.year}-8K91A2",
            defaults={
                'user': customer_user,
                'restaurant': r_ndls,
                'pnr': f"RAW-{today.year}-8F73K2",
                'train_number': '22436',
                'train_name': 'Vande Bharat Express',
                'delivery_station': bsb_stn,
                'delivery_date': today,
                'delivery_time_slot': 'On arrival at Varanasi Junction (14:00 PM)',
                'coach': 'B1',
                'seat_number': '12',
                'passenger_name': 'Rohan Sharma',
                'passenger_phone': '+91 9811223344',
                'special_instructions': 'Please pack extra paper napkins and keep food hot.',
                'base_amount': Decimal('479.00'),
                'gst': Decimal('23.95'),
                'delivery_fee': Decimal('0.00'),
                'total_amount': Decimal('502.95'),
                'status': 'CONFIRMED',
                'payment_method': 'UPI',
                'payment_status': 'PAID',
            }
        )
        if fo_created:
            f_item1 = FoodItem.objects.filter(name__icontains='Maharaja').first()
            f_item2 = FoodItem.objects.filter(name__icontains='Biryani').first()
            if f_item1:
                FoodOrderItem.objects.create(order=food_order_sample, item=f_item1, item_name=f_item1.name, is_veg=f_item1.is_veg, quantity=1, unit_price=f_item1.price, total_price=f_item1.price)
            if f_item2:
                FoodOrderItem.objects.create(order=food_order_sample, item=f_item2, item_name=f_item2.name, is_veg=f_item2.is_veg, quantity=1, unit_price=f_item2.price, total_price=f_item2.price)

        # ==========================================
        # 7. RETIRING ROOMS & DORMITORIES
        # ==========================================
        self.stdout.write("Seeding Station Retiring Rooms & Dormitories...")

        retiring_rooms_data = [
            {'station': ndls_stn, 'type': 'AC_DORMITORY', 'designation': 'Bed D-04 (Men)', 'floor': 'Platform 1, 1st Floor Concourse', 'p12': Decimal('250.00'), 'p24': Decimal('450.00'), 'p48': Decimal('850.00'), 'cap': 1, 'img': 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=800&auto=format&fit=crop&q=80'},
            {'station': ndls_stn, 'type': 'AC_DELUXE', 'designation': 'Room 204', 'floor': 'Main Station Building, 2nd Floor', 'p12': Decimal('1100.00'), 'p24': Decimal('1850.00'), 'p48': Decimal('3400.00'), 'cap': 2, 'img': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80'},
            {'station': ndls_stn, 'type': 'EXECUTIVE_SUITE', 'designation': 'Suite 101', 'floor': 'VIP Executive Lounge Concourse', 'p12': Decimal('1800.00'), 'p24': Decimal('3200.00'), 'p48': Decimal('5800.00'), 'cap': 3, 'img': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80'},
            
            {'station': bsb_stn, 'type': 'AC_DORMITORY', 'designation': 'Dorm Bed 08', 'floor': 'Cantt Building, 1st Floor', 'p12': Decimal('200.00'), 'p24': Decimal('380.00'), 'p48': Decimal('700.00'), 'cap': 1, 'img': 'https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=800&auto=format&fit=crop&q=80'},
            {'station': bsb_stn, 'type': 'AC_DELUXE', 'designation': 'Deluxe Room 102', 'floor': 'Platform 1 Concourse', 'p12': Decimal('950.00'), 'p24': Decimal('1600.00'), 'p48': Decimal('2900.00'), 'cap': 2, 'img': 'https://images.unsplash.com/photo-1566665797739-1674de7a421a?w=800&auto=format&fit=crop&q=80'},

            {'station': bom_stn, 'type': 'AC_DORMITORY', 'designation': 'Pod Bed P-12', 'floor': 'Platform 1, Modern Pod Hotel Block', 'p12': Decimal('350.00'), 'p24': Decimal('650.00'), 'p48': Decimal('1200.00'), 'cap': 1, 'img': 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?w=800&auto=format&fit=crop&q=80'},
            {'station': bom_stn, 'type': 'AC_DELUXE', 'designation': 'Deluxe Room 301', 'floor': 'Main Heritage Wing, 3rd Floor', 'p12': Decimal('1250.00'), 'p24': Decimal('2100.00'), 'p48': Decimal('3900.00'), 'cap': 2, 'img': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80'},

            {'station': sbc_stn, 'type': 'AC_DORMITORY', 'designation': 'AC Bed D-02', 'floor': 'Platform 1 West Entry, 1st Floor', 'p12': Decimal('280.00'), 'p24': Decimal('490.00'), 'p48': Decimal('900.00'), 'cap': 1, 'img': 'https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?w=800&auto=format&fit=crop&q=80'},
            {'station': sbc_stn, 'type': 'NON_AC_STANDARD', 'designation': 'Standard Room 105', 'floor': 'Main Concourse, 1st Floor', 'p12': Decimal('450.00'), 'p24': Decimal('750.00'), 'p48': Decimal('1350.00'), 'cap': 2, 'img': 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800&auto=format&fit=crop&q=80'},
        ]

        for rrd in retiring_rooms_data:
            StationRetiringRoom.objects.get_or_create(
                station=rrd['station'],
                room_or_bed_no=rrd['designation'],
                defaults={
                    'room_type': rrd['type'],
                    'floor': rrd['floor'],
                    'price_12h': rrd['p12'],
                    'price_24h': rrd['p24'],
                    'price_48h': rrd['p48'],
                    'capacity': rrd['cap'],
                    'image_url': rrd['img'],
                    'is_active': True,
                }
            )

        # Sample Retiring Room Booking for Rohan
        sample_rr = StationRetiringRoom.objects.filter(station=bsb_stn).first()
        if sample_rr:
            RetiringRoomBooking.objects.get_or_create(
                booking_ref=f"RR-BSB-8812A",
                defaults={
                    'user': customer_user,
                    'station': bsb_stn,
                    'room': sample_rr,
                    'slot_type': '24_HOURS',
                    'check_in_date': today,
                    'check_in_time_slot': '08:00 AM - 08:00 PM',
                    'check_out_date': today + timedelta(days=1),
                    'guest_count': 1,
                    'guest_name': 'Rohan Sharma',
                    'guest_age': 29,
                    'guest_gender': 'MALE',
                    'guest_phone': '+91 9811223344',
                    'guest_email': 'customer@railaway.com',
                    'guest_id_type': 'AADHAAR',
                    'guest_id_number': '541298761234',
                    'train_pnr': f"RAW-{today.year}-8F73K2",
                    'base_amount': sample_rr.price_24h,
                    'taxes': Decimal('50.00'),
                    'total_amount': sample_rr.price_24h + Decimal('50.00'),
                    'booking_status': 'CONFIRMED',
                    'payment_status': 'SUCCESS',
                    'payment_method': 'UPI',
                }
            )

        # ==========================================
        # 8. CUSTOMER REVIEWS & EXPERIENCES
        # ==========================================
        self.stdout.write("Seeding Customer Reviews & Verified Traveler Feedback...")

        reviews_data = [
            {
                'name': 'Aarav Singhania', 'city': 'New Delhi', 'type': 'TRAIN', 'pnr': f"RAW-{today.year}-8F73K2",
                'service': 'Vande Bharat Express (22436)', 'rating': 5,
                'title': 'Smooth 160 km/h ride with spotless coaches and great food!',
                'text': 'Booked Executive AC seats via RailAway. Seat layout was crystal clear on the interactive coach map. The train was dead on time and automatic doors made boarding seamless.',
                'punctuality': 5, 'cleanliness': 5, 'service': 5, 'value': 5, 'tag': 'Solo Business Trip', 'votes': 42, 'featured': True
            },
            {
                'name': 'Priyanka Sen', 'city': 'Kolkata', 'type': 'FOOD', 'pnr': f"RAW-{today.year}-8K91A2",
                'service': 'IRCTC Food Plaza (BSB)', 'rating': 5,
                'title': 'Hot Maharaja Thali delivered directly to my berth at Varanasi!',
                'text': 'Ordered the Maharaja Thali with zero hassle. The delivery runner reached my coach B1 right as the train touched the platform. Food was piping hot and sealed tamper-proof.',
                'punctuality': 5, 'cleanliness': 5, 'service': 5, 'value': 5, 'tag': 'Family Vacation', 'votes': 38, 'featured': True
            },
            {
                'name': 'Vikram Rathore', 'city': 'Jaipur', 'type': 'RETIRING_ROOM', 'pnr': f"RR-NDLS-8812A",
                'service': 'NDLS Concourse Deluxe Room', 'rating': 5,
                'title': 'Super clean AC room at New Delhi station for my 12-hour transit.',
                'text': 'Having an on-platform room saved me hours of hotel commute. Free high-speed WiFi, clean bed linen, hot water shower, and 24/7 security. Unbeatable value for transit.',
                'punctuality': 5, 'cleanliness': 5, 'service': 5, 'value': 5, 'tag': 'Transit Passenger', 'votes': 29, 'featured': True
            },
            {
                'name': 'Ananya Deshmukh', 'city': 'Pune', 'type': 'BUS', 'pnr': f"RAW-{today.year}-5T7B99",
                'service': 'Zingbus Luxury Volvo Multi-Axle', 'rating': 5,
                'title': 'Comfortable sleeper deck from Pune to Goa with live GPS tracking!',
                'text': 'The upper single berth was super cozy with clean blankets and charging ports. Zero double-booking glitches and on-time arrival at Mapusa.',
                'punctuality': 5, 'cleanliness': 5, 'service': 5, 'value': 4, 'tag': 'Weekend Getaway', 'votes': 24, 'featured': True
            },
            {
                'name': 'Karthik Ramanathan', 'city': 'Chennai', 'type': 'HOTEL', 'pnr': 'HTL-GOA-9921',
                'service': 'The Heritage Palace Resort Goa', 'rating': 5,
                'title': 'Gorgeous heritage stay with instant check-in confirmation voucher.',
                'text': 'Booked standard deluxe room with breakfast included. The instant voucher barcode made our check-in seamless without any paperwork delay.',
                'punctuality': 5, 'cleanliness': 5, 'service': 5, 'value': 5, 'tag': 'Honeymoon Trip', 'votes': 31, 'featured': True
            },
            {
                'name': 'Meera Kapoor', 'city': 'Bengaluru', 'type': 'FLIGHT', 'pnr': f"RAW-{today.year}-99XK14",
                'service': 'Air India AI-805 (BLR -> DEL)', 'rating': 5,
                'title': 'Lowest fare comparison saved me ₹1,200 on my flight ticket!',
                'text': 'Used RailAway Price Finder to compare train vs flight. Found the cheapest morning economy flight with free meal included. Instant boarding pass generated!',
                'punctuality': 5, 'cleanliness': 5, 'service': 5, 'value': 5, 'tag': 'Business Commute', 'votes': 56, 'featured': True
            },
        ]

        for rev in reviews_data:
            CustomerReview.objects.get_or_create(
                title=rev['title'],
                reviewer_name=rev['name'],
                defaults={
                    'user': customer_user,
                    'reviewer_city': rev['city'],
                    'booking_type': rev['type'],
                    'pnr_or_ref': rev['pnr'],
                    'service_name': rev['service'],
                    'rating': rev['rating'],
                    'review_text': rev['text'],
                    'punctuality_rating': rev['punctuality'],
                    'cleanliness_rating': rev['cleanliness'],
                    'service_rating': rev['service'],
                    'value_rating': rev['value'],
                    'verified_traveler': True,
                    'travel_tag': rev['tag'],
                    'helpful_votes': rev['votes'],
                    'is_featured': rev['featured'],
                }
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully for RailAway!"))
        self.stdout.write(self.style.SUCCESS("Demo Admin Account: admin / admin123"))
        self.stdout.write(self.style.SUCCESS("Demo Customer Account: customer / password123"))
