from decimal import Decimal
from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from hotels.models import HotelAmenity, Hotel, HotelImage, Room, HotelReview


class Command(BaseCommand):
    help = 'Seeds rich hotel data across major Indian destinations with rooms, amenities, photos, and reviews'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Hotel Booking inventory..."))

        # 1. Amenities
        amenities_data = [
            {'name': 'Free High-Speed Wi-Fi', 'icon_class': 'fa-solid fa-wifi', 'description': 'Seamless fiber broadband in all rooms and public areas'},
            {'name': 'Swimming Pool', 'icon_class': 'fa-solid fa-person-swimming', 'description': 'Temperature controlled outdoor & indoor pools'},
            {'name': 'Complimentary Breakfast', 'icon_class': 'fa-solid fa-utensils', 'description': 'Sumptuous Indian & Continental buffet breakfast'},
            {'name': '24/7 Room Service', 'icon_class': 'fa-solid fa-bell-concierge', 'description': 'Round-the-clock gourmet in-room dining'},
            {'name': 'Spa & Ayurvedic Wellness', 'icon_class': 'fa-solid fa-spa', 'description': 'Holistic therapies and relaxing massage rituals'},
            {'name': 'Fitness Center & Gym', 'icon_class': 'fa-solid fa-dumbbell', 'description': 'Fully equipped modern gym with personal trainers'},
            {'name': 'Free Valet Parking', 'icon_class': 'fa-solid fa-square-parking', 'description': 'Secure covered parking with EV charging stations'},
            {'name': 'Airport Shuttle Transfer', 'icon_class': 'fa-solid fa-van-shuttle', 'description': 'Chauffeured luxury pickup and drop service'},
            {'name': 'Multi-Cuisine Restaurant', 'icon_class': 'fa-solid fa-bowl-food', 'description': 'Award-winning fine dining restaurants and rooftop bars'},
            {'name': 'Air Conditioning', 'icon_class': 'fa-solid fa-snowflake', 'description': 'Individual climate control in every room'},
            {'name': 'Business Center & Lounge', 'icon_class': 'fa-solid fa-briefcase', 'description': 'High-tech meeting spaces, printing, and conference facilities'},
            {'name': 'Doctor on Call', 'icon_class': 'fa-solid fa-user-doctor', 'description': '24/7 medical assistance and on-demand doctor visits'},
        ]

        amenity_objs = {}
        for a in amenities_data:
            obj, _ = HotelAmenity.objects.get_or_create(name=a['name'], defaults=a)
            amenity_objs[a['name']] = obj

        # Demo Users for Reviews
        user_customer, _ = User.objects.get_or_create(username='customer', defaults={'first_name': 'Rohan', 'last_name': 'Sharma'})
        user_ananya, _ = User.objects.get_or_create(username='ananya', defaults={'first_name': 'Ananya', 'last_name': 'Patel'})
        user_admin, _ = User.objects.get_or_create(username='admin', defaults={'first_name': 'System', 'last_name': 'Admin'})

        # 2. Hotels Data
        hotels_data = [
            # NEW DELHI
            {
                'name': 'The Imperial Heritage Palace',
                'tagline': 'Timeless Victorian Grandeur in the Heart of New Delhi',
                'hotel_type': 'HERITAGE',
                'star_rating': 5,
                'guest_rating': Decimal('4.8'),
                'review_count': 342,
                'city': 'New Delhi',
                'state': 'Delhi',
                'address': 'Janpath, Connaught Place, New Delhi - 110001',
                'pincode': '110001',
                'landmark': '5 mins from New Delhi Railway Station (NDLS) & Shivaji Stadium Metro',
                'description': 'An iconic 1930s heritage luxury sanctuary blending colonial elegance with contemporary world-class hospitality. Nestled in lush 8-acre landscaped gardens, it features renowned art collections, 7 fine-dining restaurants, and an award-winning spa.',
                'main_image': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&auto=format&fit=crop&q=80',
                'gallery': [
                    ('https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80', 'Luxury Royal Suite'),
                    ('https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&auto=format&fit=crop&q=80', 'Courtyard & Swimming Pool'),
                    ('https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=800&auto=format&fit=crop&q=80', 'Grand Lobby & Lounge'),
                ],
                'amenities': ['Free High-Speed Wi-Fi', 'Swimming Pool', 'Complimentary Breakfast', '24/7 Room Service', 'Spa & Ayurvedic Wellness', 'Fitness Center & Gym', 'Free Valet Parking', 'Multi-Cuisine Restaurant', 'Air Conditioning', 'Airport Shuttle Transfer'],
                'is_featured': True,
                'rooms': [
                    {
                        'room_type': 'Heritage Superior Room',
                        'bed_type': '1 King Bed or 2 Twin Beds',
                        'room_size_sqft': 360,
                        'max_adults': 2,
                        'max_children': 1,
                        'max_occupancy': 3,
                        'price_per_night': Decimal('5499.00'),
                        'discounted_price': Decimal('4999.00'),
                        'total_rooms': 20,
                        'available_rooms': 18,
                        'image_url': 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'custom_facilities': 'High-speed Wi-Fi, 55" Smart LED TV, Italian Marble Bathroom, Luxury Toiletries, Tea/Coffee Maker, Mini Bar'
                    },
                    {
                        'room_type': 'Grand Heritage Suite',
                        'bed_type': '1 Four-Poster King Bed',
                        'room_size_sqft': 650,
                        'max_adults': 3,
                        'max_children': 2,
                        'max_occupancy': 4,
                        'price_per_night': Decimal('9999.00'),
                        'discounted_price': Decimal('8999.00'),
                        'total_rooms': 10,
                        'available_rooms': 8,
                        'image_url': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'has_city_view': True,
                        'custom_facilities': 'Separate Living Room, Victorian Bathtub, Butler Service, Nespresso Machine, Complimentary Evening Cocktails'
                    }
                ],
                'reviews': [
                    {'user': user_customer, 'rating': 5, 'title': 'Unmatched Royal Experience in Delhi!', 'comment': 'Stayed here for 3 nights after our Shatabdi train arrival. The proximity to NDLS station and Connaught Place is unbeatable. Breakfast spread was outstanding!'},
                    {'user': user_ananya, 'rating': 5, 'title': 'Heritage Charm with 5-Star Comfort', 'comment': 'Super clean rooms, courteous staff, and breathtaking architecture. Highly recommend the Grand Suite.'}
                ]
            },
            {
                'name': 'Radisson Blu Aerocity Plaza',
                'tagline': 'Contemporary 5-Star Luxury Minutes from IGI Airport',
                'hotel_type': 'BUSINESS',
                'star_rating': 5,
                'guest_rating': Decimal('4.6'),
                'review_count': 210,
                'city': 'New Delhi',
                'state': 'Delhi',
                'address': 'Asset No. 4, Aerocity Hospitality District, New Delhi - 110037',
                'pincode': '110037',
                'landmark': '5 mins from Indira Gandhi International Airport (DEL) Terminal 3',
                'description': 'Designed for sophisticated business and leisure travelers, offering soundproof rooms, high-speed connectivity, an outdoor swimming pool, 24/7 fitness club, and easy access to both Delhi and Cyber City Gurugram.',
                'main_image': 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=1200&auto=format&fit=crop&q=80',
                'gallery': [
                    ('https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80', 'Executive Room'),
                    ('https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&auto=format&fit=crop&q=80', 'Pool & Wellness Club'),
                ],
                'amenities': ['Free High-Speed Wi-Fi', 'Swimming Pool', 'Complimentary Breakfast', '24/7 Room Service', 'Fitness Center & Gym', 'Free Valet Parking', 'Airport Shuttle Transfer', 'Air Conditioning', 'Business Center & Lounge'],
                'is_featured': False,
                'rooms': [
                    {
                        'room_type': 'Deluxe Business King',
                        'bed_type': '1 King Bed',
                        'room_size_sqft': 340,
                        'max_adults': 2,
                        'max_children': 1,
                        'max_occupancy': 3,
                        'price_per_night': Decimal('4299.00'),
                        'discounted_price': Decimal('3899.00'),
                        'total_rooms': 30,
                        'available_rooms': 25,
                        'image_url': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'custom_facilities': 'Soundproof Windows, Work Desk, Ergonomic Chair, LED TV, Rain Shower, Electronic Safe'
                    }
                ],
                'reviews': [
                    {'user': user_customer, 'rating': 4, 'title': 'Perfect Transit Stay before Flight', 'comment': 'Seamless shuttle transfer from T3. Quiet and comfortable sleep.'}
                ]
            },

            # MUMBAI
            {
                'name': 'Taj Lands End Luxury Marine Resort',
                'tagline': 'Panoramic Arabian Sea Views & Legendary Taj Hospitality',
                'hotel_type': 'LUXURY',
                'star_rating': 5,
                'guest_rating': Decimal('4.9'),
                'review_count': 580,
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'address': 'BJ Road, Bandstand, Bandra West, Mumbai - 400050',
                'pincode': '400050',
                'landmark': 'Overlooking Bandra-Worli Sea Link & Bandstand Promenade',
                'description': 'Perched majestically at the tip of Bandra Bandstand with spellbinding views of the Arabian Sea. Boasting award-winning dining (Ming Yang, Masala Bay, Vista), Jiva Spa, and seaside infinity pools.',
                'main_image': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=1200&auto=format&fit=crop&q=80',
                'gallery': [
                    ('https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80', 'Sea View Suite'),
                    ('https://images.unsplash.com/photo-1540541338287-41700207dee6?w=800&auto=format&fit=crop&q=80', 'Infinity Pool at Sunset'),
                ],
                'amenities': ['Free High-Speed Wi-Fi', 'Swimming Pool', 'Complimentary Breakfast', '24/7 Room Service', 'Spa & Ayurvedic Wellness', 'Fitness Center & Gym', 'Free Valet Parking', 'Multi-Cuisine Restaurant', 'Air Conditioning', 'Airport Shuttle Transfer'],
                'is_featured': True,
                'rooms': [
                    {
                        'room_type': 'Deluxe Arabian Sea View Room',
                        'bed_type': '1 King Bed or 2 Twin Beds',
                        'room_size_sqft': 400,
                        'max_adults': 2,
                        'max_children': 1,
                        'max_occupancy': 3,
                        'price_per_night': Decimal('7999.00'),
                        'discounted_price': Decimal('7199.00'),
                        'total_rooms': 25,
                        'available_rooms': 20,
                        'image_url': 'https://images.unsplash.com/photo-1591088398332-8a7791972843?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'has_city_view': True,
                        'custom_facilities': 'Full Ocean View, Deep Soaking Tub, High-speed Wi-Fi, 55" Smart TV, Nespresso Machine, Pillow Menu'
                    },
                    {
                        'room_type': 'Taj Club Luxury Suite',
                        'bed_type': '1 King Bed',
                        'room_size_sqft': 750,
                        'max_adults': 3,
                        'max_children': 1,
                        'max_occupancy': 4,
                        'price_per_night': Decimal('14999.00'),
                        'discounted_price': Decimal('13499.00'),
                        'total_rooms': 8,
                        'available_rooms': 6,
                        'image_url': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'has_city_view': True,
                        'has_balcony': True,
                        'custom_facilities': 'Club Lounge Access, High Tea & Evening Cocktails, 24-hour Butler, Luxury Airport Limousine'
                    }
                ],
                'reviews': [
                    {'user': user_customer, 'rating': 5, 'title': 'Spectacular Sunset & Royal Hospitality', 'comment': 'The ocean view from our room was mesmerizing. Breakfast at Vista was extraordinary.'},
                    {'user': user_ananya, 'rating': 5, 'title': 'Best Luxury Stay in Mumbai', 'comment': 'Taj service is in a class of its own. Everything from check-in to check-out was flawless.'}
                ]
            },

            # JAIPUR
            {
                'name': 'Rambagh Heritage Palace Jaipur',
                'tagline': 'The Jewel of Jaipur — Live Like Royalty in the Maharaja’s Palace',
                'hotel_type': 'HERITAGE',
                'star_rating': 5,
                'guest_rating': Decimal('4.9'),
                'review_count': 490,
                'city': 'Jaipur',
                'state': 'Rajasthan',
                'address': 'Bhawani Singh Road, Jaipur - 302005',
                'pincode': '302005',
                'landmark': 'Near Central Museum & 4 km from Jaipur Junction Railway Station (JP)',
                'description': 'Formerly the residence of the Maharaja of Jaipur, Rambagh Palace is acclaimed among the finest hotels in the world. Set across 47 acres of landscaped Mughal gardens with peacock walkways, marble corridors, and royal dining.',
                'main_image': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&auto=format&fit=crop&q=80',
                'gallery': [
                    ('https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80', 'Maharaja Suite'),
                    ('https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800&auto=format&fit=crop&q=80', 'Palace Courtyard & Peacocks'),
                ],
                'amenities': ['Free High-Speed Wi-Fi', 'Swimming Pool', 'Complimentary Breakfast', '24/7 Room Service', 'Spa & Ayurvedic Wellness', 'Fitness Center & Gym', 'Free Valet Parking', 'Multi-Cuisine Restaurant', 'Air Conditioning', 'Airport Shuttle Transfer'],
                'is_featured': True,
                'rooms': [
                    {
                        'room_type': 'Palace Room (Garden View)',
                        'bed_type': '1 King Bed',
                        'room_size_sqft': 500,
                        'max_adults': 2,
                        'max_children': 1,
                        'max_occupancy': 3,
                        'price_per_night': Decimal('8999.00'),
                        'discounted_price': Decimal('7999.00'),
                        'total_rooms': 15,
                        'available_rooms': 12,
                        'image_url': 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'has_city_view': True,
                        'custom_facilities': 'Carved Marble Architecture, Four-Poster Bed, Walk-in Dressing Area, Royal Welcome, Heritage Turndown Service'
                    }
                ],
                'reviews': [
                    {'user': user_ananya, 'rating': 5, 'title': 'Truly a royal dream!', 'comment': 'The palace is magical. Peacocks roaming the lawns in the morning made our holiday unforgettable.'}
                ]
            },

            # GOA
            {
                'name': 'Taj Exotica Beach Resort & Spa Goa',
                'tagline': '56 Acres of Mediterranean Elegance on Benaulim Beach',
                'hotel_type': 'RESORT',
                'star_rating': 5,
                'guest_rating': Decimal('4.8'),
                'review_count': 610,
                'city': 'Goa',
                'state': 'Goa',
                'address': 'Calwaddo, Benaulim, South Goa - 403716',
                'pincode': '403716',
                'landmark': 'Direct beachfront access to pristine Benaulim Beach',
                'description': 'Spread across 56 lush acres along the southwest coast of Goa, overlooking the Arabian Sea. Features Mediterranean architecture, sprawling lawns, private pool villas, sea-facing dining (Lobster Village), and 9-hole golf greens.',
                'main_image': 'https://images.unsplash.com/photo-1540541338287-41700207dee6?w=1200&auto=format&fit=crop&q=80',
                'gallery': [
                    ('https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&auto=format&fit=crop&q=80', 'Beachside Villa'),
                    ('https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80', 'Luxury Room with Balcony'),
                ],
                'amenities': ['Free High-Speed Wi-Fi', 'Swimming Pool', 'Complimentary Breakfast', '24/7 Room Service', 'Spa & Ayurvedic Wellness', 'Fitness Center & Gym', 'Free Valet Parking', 'Multi-Cuisine Restaurant', 'Air Conditioning', 'Airport Shuttle Transfer'],
                'is_featured': True,
                'rooms': [
                    {
                        'room_type': 'Premium Sea View Villa Room',
                        'bed_type': '1 King Bed',
                        'room_size_sqft': 550,
                        'max_adults': 3,
                        'max_children': 1,
                        'max_occupancy': 4,
                        'price_per_night': Decimal('6999.00'),
                        'discounted_price': Decimal('6299.00'),
                        'total_rooms': 20,
                        'available_rooms': 15,
                        'image_url': 'https://images.unsplash.com/photo-1540541338287-41700207dee6?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'has_balcony': True,
                        'custom_facilities': 'Private Verandah, Direct Garden/Beach Access, Sun Loungers, Rain Shower, Free Minibar Snacks'
                    }
                ],
                'reviews': [
                    {'user': user_customer, 'rating': 5, 'title': 'Heaven in South Goa', 'comment': 'Serene, clean private beach, and top notch food. Our best Goa vacation ever.'}
                ]
            },

            # BENGALURU
            {
                'name': 'The Leela Palace Bengaluru',
                'tagline': 'Modern Royalty Amidst 7 Acres of Lush Gardens',
                'hotel_type': 'LUXURY',
                'star_rating': 5,
                'guest_rating': Decimal('4.8'),
                'review_count': 320,
                'city': 'Bengaluru',
                'state': 'Karnataka',
                'address': '23 Old Airport Road, Kodihalli, Bengaluru - 560008',
                'pincode': '560008',
                'landmark': 'Near Indiranagar & KSR Bengaluru Junction (SBC)',
                'description': 'Inspired by the architectural opulence of the Royal Palace of Mysore, featuring ornate copper domes, arches, and hand-woven silk carpets. Located close to the city tech corridors.',
                'main_image': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&auto=format&fit=crop&q=80',
                'gallery': [
                    ('https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80', 'Royal Premier Room'),
                ],
                'amenities': ['Free High-Speed Wi-Fi', 'Swimming Pool', 'Complimentary Breakfast', '24/7 Room Service', 'Spa & Ayurvedic Wellness', 'Fitness Center & Gym', 'Free Valet Parking', 'Multi-Cuisine Restaurant', 'Air Conditioning', 'Business Center & Lounge'],
                'is_featured': True,
                'rooms': [
                    {
                        'room_type': 'Royal Premier King Room',
                        'bed_type': '1 King Bed',
                        'room_size_sqft': 520,
                        'max_adults': 2,
                        'max_children': 1,
                        'max_occupancy': 3,
                        'price_per_night': Decimal('6499.00'),
                        'discounted_price': Decimal('5799.00'),
                        'total_rooms': 22,
                        'available_rooms': 18,
                        'image_url': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'has_balcony': True,
                        'custom_facilities': 'Private Balcony overlooking Gardens, Marble Bath, Deep Soaking Tub, 55" Smart TV'
                    }
                ],
                'reviews': [
                    {'user': user_customer, 'rating': 5, 'title': 'Majestic Property', 'comment': 'One of the grandest hotels in India. Citrus restaurant breakfast was fantastic.'}
                ]
            },

            # VARANASI
            {
                'name': 'BrijRama Palace Heritage Ghats',
                'tagline': '210-Year Old Royal Palace on Darbhanga Ghat, Varanasi',
                'hotel_type': 'HERITAGE',
                'star_rating': 5,
                'guest_rating': Decimal('4.9'),
                'review_count': 295,
                'city': 'Varanasi',
                'state': 'Uttar Pradesh',
                'address': 'Darbhanga Ghat, Dashashwamedh, Varanasi - 221001',
                'pincode': '221001',
                'landmark': 'On the sacred River Ganga, 2 mins from Dashashwamedh Ganga Aarti Ghat',
                'description': 'One of the oldest palace structures on the riverfront ghats of Varanasi. Built in 1812, this architectural marvel offers private boat pickup, daily live classical Shehnai recitals, and pure vegetarian royal Awadhi cuisine.',
                'main_image': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&auto=format&fit=crop&q=80',
                'gallery': [
                    ('https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80', 'Ganga View Suite'),
                ],
                'amenities': ['Free High-Speed Wi-Fi', 'Complimentary Breakfast', '24/7 Room Service', 'Spa & Ayurvedic Wellness', 'Multi-Cuisine Restaurant', 'Air Conditioning', 'Doctor on Call'],
                'is_featured': True,
                'rooms': [
                    {
                        'room_type': 'Maharaja Ganga View Room',
                        'bed_type': '1 King Bed',
                        'room_size_sqft': 420,
                        'max_adults': 2,
                        'max_children': 1,
                        'max_occupancy': 3,
                        'price_per_night': Decimal('7499.00'),
                        'discounted_price': Decimal('6899.00'),
                        'total_rooms': 12,
                        'available_rooms': 10,
                        'image_url': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80',
                        'has_free_breakfast': True,
                        'has_free_cancellation': True,
                        'has_ac': True,
                        'has_wifi': True,
                        'has_city_view': True,
                        'custom_facilities': 'Direct Ganga River View, Antique Wooden Furniture, Complimentary Evening Boat Ride to Ganga Aarti'
                    }
                ],
                'reviews': [
                    {'user': user_ananya, 'rating': 5, 'title': 'Divine & Magical Experience', 'comment': 'Watching the sunrise over the Ganga from our room balcony was the most spiritual moment of our trip.'}
                ]
            }
        ]

        for h_data in hotels_data:
            rooms_list = h_data.pop('rooms', [])
            gallery_list = h_data.pop('gallery', [])
            amenity_names = h_data.pop('amenities', [])
            reviews_list = h_data.pop('reviews', [])

            hotel, created = Hotel.objects.get_or_create(
                name=h_data['name'],
                city=h_data['city'],
                defaults=h_data
            )

            # Link Amenities
            hotel.amenities.clear()
            for a_name in amenity_names:
                if a_name in amenity_objs:
                    hotel.amenities.add(amenity_objs[a_name])

            # Add Gallery Images
            hotel.gallery_images.all().delete()
            for idx, (img_url, caption) in enumerate(gallery_list):
                HotelImage.objects.create(
                    hotel=hotel,
                    image_url=img_url,
                    caption=caption,
                    display_order=idx + 1
                )

            # Add Rooms
            for r_data in rooms_list:
                Room.objects.get_or_create(
                    hotel=hotel,
                    room_type=r_data['room_type'],
                    defaults=r_data
                )

            # Add Reviews
            for rev in reviews_list:
                HotelReview.objects.get_or_create(
                    hotel=hotel,
                    user=rev['user'],
                    title=rev['title'],
                    defaults={
                        'rating': rev['rating'],
                        'comment': rev['comment'],
                        'stay_date': timezone.now().date() - timedelta(days=15)
                    }
                )

            self.stdout.write(f"  [+] Seeded Hotel: {hotel.name} ({hotel.city})")

        self.stdout.write(self.style.SUCCESS("Successfully seeded all Hotel Booking data!"))
