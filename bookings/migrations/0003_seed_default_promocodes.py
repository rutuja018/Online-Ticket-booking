from django.db import migrations
from decimal import Decimal
from datetime import date, timedelta

def seed_promo_codes(apps, schema_editor):
    PromoCode = apps.get_model('bookings', 'PromoCode')
    
    # 1. TRAVELNOW - ₹100 discount on Flight Booking (and all)
    PromoCode.objects.update_or_create(
        code='TRAVELNOW',
        defaults={
            'title': 'TravelNow Flight Special',
            'description': 'Enjoy flat ₹100 instant discount on flight ticket reservations.',
            'discount_type': 'FIXED',
            'discount_amount': Decimal('100.00'),
            'min_booking_amount': Decimal('500.00'),
            'applicable_transport': 'FLIGHT',
            'valid_from': date(2025, 1, 1),
            'valid_to': date(2030, 12, 31),
            'usage_limit': 5000,
            'used_count': 0,
            'per_user_limit': 10,
            'is_active': True,
        }
    )

    # 2. RAILAWAY100 - ₹100 discount on Railway Bookings
    PromoCode.objects.update_or_create(
        code='RAILAWAY100',
        defaults={
            'title': 'RailAway Express Discount',
            'description': 'Flat ₹100 instant discount on train and all travel bookings.',
            'discount_type': 'FIXED',
            'discount_amount': Decimal('100.00'),
            'min_booking_amount': Decimal('300.00'),
            'applicable_transport': 'ALL',
            'valid_from': date(2025, 1, 1),
            'valid_to': date(2030, 12, 31),
            'usage_limit': 5000,
            'used_count': 0,
            'per_user_limit': 10,
            'is_active': True,
        }
    )

    # 3. FIRST50 - ₹50 discount for First Time Users
    PromoCode.objects.update_or_create(
        code='FIRST50',
        defaults={
            'title': 'First Journey Welcome Offer',
            'description': 'Special ₹50 welcome discount across all travel modes.',
            'discount_type': 'FIXED',
            'discount_amount': Decimal('50.00'),
            'min_booking_amount': Decimal('150.00'),
            'applicable_transport': 'ALL',
            'valid_from': date(2025, 1, 1),
            'valid_to': date(2030, 12, 31),
            'usage_limit': 10000,
            'used_count': 0,
            'per_user_limit': 1,
            'is_active': True,
        }
    )

def unseed_promo_codes(apps, schema_editor):
    PromoCode = apps.get_model('bookings', 'PromoCode')
    PromoCode.objects.filter(code__in=['TRAVELNOW', 'RAILAWAY100', 'FIRST50']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_promocode_booking_promo_code_booking_promo_code_obj'),
    ]

    operations = [
        migrations.RunPython(seed_promo_codes, reverse_code=unseed_promo_codes),
    ]
