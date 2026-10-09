from decimal import Decimal
from datetime import datetime, date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Min, Max, Count, Avg, F
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden

from .models import Hotel, Room, HotelAmenity, HotelImage, HotelBooking, HotelGuest, HotelReview
from .forms import HotelBookingForm
from bookings.models import PromoCode
from payments.models import Payment


def hotel_list(request):
    """
    Hotel Search & Listing View with multi-attribute filtering & sorting:
    - Destination city search
    - Check-in / check-out dates calculation
    - Price range filtering
    - Star ratings & guest ratings
    - Amenities filtering
    - Sorting by Price (asc/desc), Ratings, Popularity
    """
    today = timezone.now().date()
    default_check_out = today + timedelta(days=1)

    city_query = (request.GET.get('city') or request.GET.get('destination') or '').strip()
    check_in_str = request.GET.get('check_in') or ''
    check_out_str = request.GET.get('check_out') or ''
    
    try:
        rooms_count = max(1, int(request.GET.get('rooms') or 1))
    except (ValueError, TypeError):
        rooms_count = 1

    try:
        guests_count = max(1, int(request.GET.get('guests') or 2))
    except (ValueError, TypeError):
        guests_count = 2

    # Parse and validate dates
    check_in_date = today
    check_out_date = default_check_out

    if check_in_str:
        try:
            parsed_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            if parsed_in >= today:
                check_in_date = parsed_in
        except ValueError:
            pass

    if check_out_str:
        try:
            parsed_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            if parsed_out > check_in_date:
                check_out_date = parsed_out
            else:
                check_out_date = check_in_date + timedelta(days=1)
        except ValueError:
            check_out_date = check_in_date + timedelta(days=1)
    else:
        check_out_date = check_in_date + timedelta(days=1)

    nights = max(1, (check_out_date - check_in_date).days)

    # Base Query
    hotels_qs = Hotel.objects.filter(is_active=True).prefetch_related('amenities', 'rooms')

    # Destination filter
    if city_query:
        matches = hotels_qs.filter(
            Q(city__icontains=city_query) |
            Q(name__icontains=city_query) |
            Q(state__icontains=city_query) |
            Q(address__icontains=city_query) |
            Q(landmark__icontains=city_query)
        )
        if not matches.exists() and len(city_query) >= 3:
            # Generate 2 realistic luxury hotels on demand for this destination
            clean_city = city_query.strip().title()
            h1_name = f"The Grand Palace & Resort {clean_city}"
            h2_name = f"Heritage Boutique Retreat {clean_city}"

            h1, h1_created = Hotel.objects.get_or_create(
                name=h1_name,
                defaults={
                    'tagline': f"Luxury 5-Star Stay in {clean_city}",
                    'hotel_type': 'LUXURY',
                    'star_rating': 5,
                    'guest_rating': Decimal('4.8'),
                    'review_count': 128,
                    'city': clean_city,
                    'state': 'India',
                    'address': f"Main Boulevard, {clean_city} - 400001",
                    'pincode': '400001',
                    'landmark': f"10 mins from {clean_city} Center",
                    'description': f"Experience elite 5-star hospitality, premium dining, and serene accommodations in {clean_city}.",
                    'main_image': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&auto=format&fit=crop&q=80',
                    'is_featured': True,
                    'is_active': True,
                }
            )
            if h1_created:
                Room.objects.create(
                    hotel=h1,
                    room_type='Royal Executive Deluxe Room',
                    bed_type='1 King Bed',
                    room_size_sqft=380,
                    price_per_night=Decimal('4200.00'),
                    total_rooms=15,
                    available_rooms=12,
                    has_free_breakfast=True,
                    has_free_cancellation=True,
                    image_url='https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800&auto=format&fit=crop&q=80'
                )

            h2, h2_created = Hotel.objects.get_or_create(
                name=h2_name,
                defaults={
                    'tagline': f"Charming Boutique Experience in {clean_city}",
                    'hotel_type': 'BOUTIQUE',
                    'star_rating': 4,
                    'guest_rating': Decimal('4.6'),
                    'review_count': 84,
                    'city': clean_city,
                    'state': 'India',
                    'address': f"Heritage Lane, {clean_city} - 400002",
                    'pincode': '400002',
                    'landmark': f"Near {clean_city} Central Park",
                    'description': f"Cozy boutique retreat with personalized services, rooftop cafe, and comfortable modern rooms.",
                    'main_image': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=1200&auto=format&fit=crop&q=80',
                    'is_featured': False,
                    'is_active': True,
                }
            )
            if h2_created:
                Room.objects.create(
                    hotel=h2,
                    room_type='Classic Comfort Suite',
                    bed_type='1 Queen Bed',
                    room_size_sqft=320,
                    price_per_night=Decimal('2800.00'),
                    total_rooms=10,
                    available_rooms=8,
                    has_free_breakfast=True,
                    has_free_cancellation=True,
                    image_url='https://images.unsplash.com/photo-1590490360182-c33d57733427?w=800&auto=format&fit=crop&q=80'
                )

            hotels_qs = Hotel.objects.filter(is_active=True).prefetch_related('amenities', 'rooms')

        hotels_qs = hotels_qs.filter(
            Q(city__icontains=city_query) |
            Q(name__icontains=city_query) |
            Q(state__icontains=city_query) |
            Q(address__icontains=city_query) |
            Q(landmark__icontains=city_query)
        )

    # Star rating filter
    star_ratings = request.GET.getlist('stars')
    if star_ratings:
        try:
            star_nums = [int(s) for s in star_ratings if s.isdigit()]
            if star_nums:
                hotels_qs = hotels_qs.filter(star_rating__in=star_nums)
        except Exception:
            pass

    # Single star_rating query param support
    single_star = request.GET.get('star_rating')
    if single_star and single_star.isdigit():
        hotels_qs = hotels_qs.filter(star_rating=int(single_star))

    # Hotel Type filter
    hotel_types = request.GET.getlist('hotel_type')
    if hotel_types:
        hotels_qs = hotels_qs.filter(hotel_type__in=hotel_types)

    # Guest rating filter (e.g. 4.5+, 4.0+, 3.5+)
    min_guest_rating = request.GET.get('min_rating')
    if min_guest_rating:
        try:
            r_val = float(min_guest_rating)
            hotels_qs = hotels_qs.filter(guest_rating__gte=Decimal(str(r_val)))
        except (ValueError, TypeError):
            pass

    # Amenities filter
    selected_amenity_ids = request.GET.getlist('amenities')
    if selected_amenity_ids:
        for a_id in selected_amenity_ids:
            if a_id.isdigit():
                hotels_qs = hotels_qs.filter(amenities__id=int(a_id))

    # Price range filter
    min_price_param = request.GET.get('min_price')
    max_price_param = request.GET.get('max_price')

    if min_price_param and min_price_param.isdigit():
        min_p = Decimal(min_price_param)
        hotels_qs = hotels_qs.filter(rooms__price_per_night__gte=min_p).distinct()

    if max_price_param and max_price_param.isdigit():
        max_p = Decimal(max_price_param)
        hotels_qs = hotels_qs.filter(rooms__price_per_night__lte=max_p).distinct()

    # Free breakfast filter
    if request.GET.get('free_breakfast') == '1':
        hotels_qs = hotels_qs.filter(rooms__has_free_breakfast=True).distinct()

    # Free cancellation filter
    if request.GET.get('free_cancellation') == '1':
        hotels_qs = hotels_qs.filter(rooms__has_free_cancellation=True).distinct()

    # Sorting
    sort_by = request.GET.get('sort', 'recommended')
    if sort_by == 'price_low_high':
        hotels = sorted(list(hotels_qs), key=lambda h: h.min_price)
    elif sort_by == 'price_high_low':
        hotels = sorted(list(hotels_qs), key=lambda h: h.min_price, reverse=True)
    elif sort_by == 'rating_desc':
        hotels = list(hotels_qs.order_by('-guest_rating', '-review_count'))
    elif sort_by == 'stars_desc':
        hotels = list(hotels_qs.order_by('-star_rating', '-guest_rating'))
    else: # recommended / popularity
        hotels = list(hotels_qs.order_by('-is_featured', '-guest_rating', '-review_count'))

    # Calculate total stay prices
    hotel_cards = []
    for h in hotels:
        min_night_price = h.min_price
        total_stay_price = (min_night_price * Decimal(nights) * Decimal(rooms_count))
        tax_est = round(total_stay_price * Decimal('0.12'), 2)
        total_with_tax = total_stay_price + tax_est + Decimal('49.00')

        hotel_cards.append({
            'hotel': h,
            'min_price': min_night_price,
            'total_stay_price': total_stay_price,
            'total_with_tax': total_with_tax,
            'nights': nights,
            'rooms_count': rooms_count,
            'guests_count': guests_count,
        })

    # Available cities & all amenities for filter panel
    all_cities = sorted(list(set(Hotel.objects.filter(is_active=True).values_list('city', flat=True))))
    all_amenities = HotelAmenity.objects.all().order_by('name')

    context = {
        'hotel_cards': hotel_cards,
        'hotels_count': len(hotel_cards),
        'city': city_query,
        'check_in': check_in_date.isoformat(),
        'check_out': check_out_date.isoformat(),
        'nights': nights,
        'rooms': rooms_count,
        'guests': guests_count,
        'today': today.isoformat(),
        'default_check_out': default_check_out.isoformat(),
        'all_cities': all_cities,
        'all_amenities': all_amenities,
        'selected_stars': star_ratings,
        'selected_amenities': [int(a) for a in selected_amenity_ids if a.isdigit()],
        'selected_sort': sort_by,
        'min_price': min_price_param or '',
        'max_price': max_price_param or '',
        'min_rating': min_guest_rating or '',
        'hotel_types': Hotel.HOTEL_TYPE_CHOICES,
        'selected_hotel_types': hotel_types,
    }
    return render(request, 'hotels/list.html', context)


def hotel_detail(request, hotel_id):
    """
    Detailed Hotel View with:
    - Photo gallery
    - Detailed amenities list
    - Available Room categories with live price & features
    - Check-in/out policies & House rules
    - Guest reviews
    """
    hotel = get_object_or_404(
        Hotel.objects.prefetch_related('amenities', 'gallery_images', 'reviews', 'reviews__user', 'rooms'),
        id=hotel_id, is_active=True
    )

    today = timezone.now().date()
    default_check_out = today + timedelta(days=1)

    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')
    
    try:
        rooms_count = max(1, int(request.GET.get('rooms') or 1))
    except (ValueError, TypeError):
        rooms_count = 1

    try:
        guests_count = max(1, int(request.GET.get('guests') or 2))
    except (ValueError, TypeError):
        guests_count = 2

    check_in_date = today
    check_out_date = default_check_out

    if check_in_str:
        try:
            parsed_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            if parsed_in >= today:
                check_in_date = parsed_in
        except ValueError:
            pass

    if check_out_str:
        try:
            parsed_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            if parsed_out > check_in_date:
                check_out_date = parsed_out
            else:
                check_out_date = check_in_date + timedelta(days=1)
        except ValueError:
            check_out_date = check_in_date + timedelta(days=1)
    else:
        check_out_date = check_in_date + timedelta(days=1)

    nights = max(1, (check_out_date - check_in_date).days)

    active_rooms = hotel.rooms.filter(is_active=True).order_by('price_per_night')
    
    # Precalculate room pricing breakdowns
    room_data = []
    for r in active_rooms:
        base_stay = r.price_per_night * Decimal(nights) * Decimal(rooms_count)
        taxes = round(base_stay * Decimal('0.12'), 2)
        total = base_stay + taxes + Decimal('49.00')
        room_data.append({
            'room': r,
            'base_stay': base_stay,
            'taxes': taxes,
            'total': total,
            'is_available': r.available_rooms >= rooms_count,
        })

    reviews = hotel.reviews.all()
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or hotel.guest_rating

    # Similar/featured hotels in same city
    similar_hotels = Hotel.objects.filter(
        city=hotel.city, is_active=True
    ).exclude(id=hotel.id)[:3]

    context = {
        'hotel': hotel,
        'room_data': room_data,
        'reviews': reviews,
        'avg_rating': round(float(avg_rating), 1),
        'check_in': check_in_date.isoformat(),
        'check_out': check_out_date.isoformat(),
        'nights': nights,
        'rooms_count': rooms_count,
        'guests_count': guests_count,
        'today': today.isoformat(),
        'similar_hotels': similar_hotels,
    }
    return render(request, 'hotels/detail.html', context)


@login_required
def book_room(request, hotel_id, room_id):
    """
    Hotel Room Booking View:
    - Guest information form
    - Real-time stay nights calculation
    - Server-side validation
    - Concurrency-safe atomic booking creation
    """
    hotel = get_object_or_404(Hotel, id=hotel_id, is_active=True)
    room = get_object_or_404(Room, id=room_id, hotel=hotel, is_active=True)

    today = timezone.now().date()
    default_check_out = today + timedelta(days=1)

    if request.method == 'POST':
        form = HotelBookingForm(request.POST)
        if form.is_valid():
            check_in_date = form.cleaned_data['check_in_date']
            check_out_date = form.cleaned_data['check_out_date']
            room_count = form.cleaned_data['room_count']
            guest_count = form.cleaned_data['guest_count']
            primary_name = form.cleaned_data['primary_guest_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            special_requests = form.cleaned_data['special_requests']
            promo_code_str = form.cleaned_data.get('promo_code', '').strip().upper()

            nights = (check_out_date - check_in_date).days
            if nights < 1:
                messages.error(request, "Check-out date must be at least 1 day after check-in date.")
                return redirect('hotels:book_room', hotel_id=hotel.id, room_id=room.id)

            try:
                with transaction.atomic():
                    # Concurrency-safe room lock
                    room_locked = Room.objects.select_for_update().get(id=room.id)
                    if room_locked.available_rooms < room_count:
                        messages.error(
                            request,
                            f"Sorry, only {room_locked.available_rooms} {room.room_type}(s) currently available. Please select fewer rooms."
                        )
                        return redirect('hotels:detail', hotel_id=hotel.id)

                    # Compute Financials
                    price_per_night = room_locked.price_per_night
                    base_fare = price_per_night * Decimal(nights) * Decimal(room_count)
                    taxes = round(base_fare * Decimal('0.12'), 2)
                    service_fee = Decimal('49.00')
                    gross_total = base_fare + taxes + service_fee

                    # Promo validation
                    discount = Decimal('0.00')
                    applied_promo = None

                    if promo_code_str:
                        promo_obj = PromoCode.objects.filter(code=promo_code_str).first()
                        if promo_obj:
                            is_valid, promo_disc, msg = promo_obj.is_valid_for_booking(gross_total, 'ALL', request.user)
                            if is_valid:
                                applied_promo = promo_obj
                                discount = promo_disc
                            else:
                                messages.warning(request, f"Promo code could not be applied: {msg}")
                        else:
                            messages.warning(request, f"Promo code '{promo_code_str}' is invalid.")

                    final_total = max(Decimal('1.00'), gross_total - discount)

                    # Create Booking Record
                    booking = HotelBooking.objects.create(
                        user=request.user,
                        hotel=hotel,
                        room=room_locked,
                        room_count=room_count,
                        guest_count=guest_count,
                        check_in_date=check_in_date,
                        check_out_date=check_out_date,
                        nights=nights,
                        primary_guest_name=primary_name,
                        email=email,
                        phone=phone,
                        special_requests=special_requests,
                        base_price_per_night=price_per_night,
                        base_fare=base_fare,
                        taxes=taxes,
                        service_fee=service_fee,
                        discount=discount,
                        total_amount=final_total,
                        promo_code=applied_promo.code if applied_promo else (promo_code_str if discount > 0 else None),
                        promo_code_obj=applied_promo,
                        booking_status='PENDING',
                        payment_status='PENDING',
                    )

                    # Primary guest
                    HotelGuest.objects.create(
                        booking=booking,
                        full_name=primary_name,
                        is_primary=True
                    )

                    # Additional guests if provided
                    for i in range(2, guest_count + 1):
                        g_name = request.POST.get(f'guest_{i}_name', '').strip()
                        g_age = request.POST.get(f'guest_{i}_age', '')
                        g_gender = request.POST.get(f'guest_{i}_gender', 'MALE')
                        if g_name:
                            HotelGuest.objects.create(
                                booking=booking,
                                full_name=g_name,
                                age=int(g_age) if g_age.isdigit() else None,
                                gender=g_gender,
                                is_primary=False
                            )

                    # Decrement room availability
                    room_locked.available_rooms = F('available_rooms') - room_count
                    room_locked.save(update_fields=['available_rooms'])

                    return redirect('hotels:process_payment', booking_id=booking.id)

            except Exception as e:
                messages.error(request, f"An error occurred while creating your hotel booking: {str(e)}")
                return redirect('hotels:detail', hotel_id=hotel.id)
    else:
        # Prepopulate initial data from query params
        check_in_str = request.GET.get('check_in')
        check_out_str = request.GET.get('check_out')
        rooms_count = int(request.GET.get('rooms', 1))
        guests_count = int(request.GET.get('guests', 2))

        init_check_in = today
        init_check_out = default_check_out

        if check_in_str:
            try:
                init_check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if check_out_str:
            try:
                init_check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            except ValueError:
                init_check_out = init_check_in + timedelta(days=1)

        user_profile = getattr(request.user, 'profile', None)
        user_phone = user_profile.phone if user_profile else ''

        initial_data = {
            'check_in_date': init_check_in,
            'check_out_date': init_check_out,
            'room_count': rooms_count,
            'guest_count': guests_count,
            'primary_guest_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email or '',
            'phone': user_phone,
        }
        form = HotelBookingForm(initial=initial_data)

    nights = max(1, (form.initial.get('check_out_date', default_check_out) - form.initial.get('check_in_date', today)).days)
    room_count = form.initial.get('room_count', 1)
    base_fare = room.price_per_night * Decimal(nights) * Decimal(room_count)
    taxes = round(base_fare * Decimal('0.12'), 2)
    service_fee = Decimal('49.00')
    total_est = base_fare + taxes + service_fee

    context = {
        'hotel': hotel,
        'room': room,
        'form': form,
        'nights': nights,
        'room_count': room_count,
        'base_fare': base_fare,
        'taxes': taxes,
        'service_fee': service_fee,
        'total_est': total_est,
        'today': today.isoformat(),
        'default_check_out': default_check_out.isoformat(),
    }
    return render(request, 'hotels/book.html', context)


@login_required
def hotel_process_payment(request, booking_id):
    """
    Simulated Payment Checkout for Hotel Bookings:
    - Displays booking review & fare breakdown
    - Supports Credit Card, Debit Card, UPI, Net Banking
    - Simulates success / failure
    """
    booking = get_object_or_404(
        HotelBooking.objects.select_related('hotel', 'room', 'user').prefetch_related('guests'),
        id=booking_id
    )

    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have access to this payment session.")

    if booking.booking_status == 'CONFIRMED':
        messages.info(request, "This hotel reservation is already confirmed.")
        return redirect('hotels:confirmation', booking_ref=booking.booking_reference)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'CREDIT_CARD')
        simulate_action = request.POST.get('simulate_action', 'SUCCESS')

        card_number = request.POST.get('card_number', '').replace(' ', '')
        card_network = request.POST.get('card_network', 'Visa')
        bank_name = request.POST.get('bank_name', 'State Bank of India')
        upi_id = request.POST.get('upi_id', 'user@upi')

        if simulate_action == 'FAIL':
            booking.payment_status = 'FAILED'
            booking.save(update_fields=['payment_status'])
            messages.error(request, "Simulated payment failed as requested. You can retry with another payment method.")
            return render(request, 'hotels/payment.html', {'booking': booking})

        # Process SUCCESS
        with transaction.atomic():
            booking.booking_status = 'CONFIRMED'
            booking.payment_status = 'SUCCESS'
            booking.save(update_fields=['booking_status', 'payment_status', 'updated_at'])

            if booking.promo_code_obj:
                from bookings.models import PromoCode
                PromoCode.objects.filter(id=booking.promo_code_obj_id).update(used_count=F('used_count') + 1)

        messages.success(
            request,
            f"Payment of ₹{booking.total_amount} successful! Your hotel booking reference is {booking.booking_reference}."
        )
        return redirect('hotels:confirmation', booking_ref=booking.booking_reference)

    context = {
        'booking': booking,
    }
    return render(request, 'hotels/payment.html', context)


@login_required
def hotel_booking_confirmation(request, booking_ref):
    """
    Hotel Confirmation Voucher View:
    - Official RailAway Hotel E-Voucher
    - Printable layout with 1-click window.print()
    - Full breakdown of hotel info, dates, guest details, pricing
    """
    booking = get_object_or_404(
        HotelBooking.objects.select_related('hotel', 'room', 'user').prefetch_related('guests'),
        booking_reference=booking_ref
    )

    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have access to view this reservation.")

    can_cancel, reason_msg = booking.can_be_cancelled()

    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'reason_msg': reason_msg,
    }
    return render(request, 'hotels/confirmation.html', context)


@login_required
def hotel_booking_cancel(request, booking_ref):
    """
    Hotel Booking Cancellation View:
    - Cancellation policy breakdown
    - Estimated refund calculation
    - Releases room inventory back to hotel
    """
    booking = get_object_or_404(
        HotelBooking.objects.select_related('hotel', 'room', 'user'),
        booking_reference=booking_ref
    )

    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to cancel this booking.")

    can_cancel, reason_msg = booking.can_be_cancelled()
    estimated_refund = booking.calculate_refund() if can_cancel else Decimal('0.00')

    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', 'Customer requested cancellation')
        success, message = booking.cancel_and_release_rooms(reason=cancellation_reason)
        if success:
            messages.success(request, message)
            return redirect('hotels:confirmation', booking_ref=booking.booking_reference)
        else:
            messages.error(request, message)

    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'reason_msg': reason_msg,
        'estimated_refund': estimated_refund,
    }
    return render(request, 'hotels/cancel.html', context)


def hotel_validate_promo(request):
    """
    AJAX endpoint to validate promo codes for hotel bookings in real-time.
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'valid': False, 'message': 'Invalid request method.'}, status=405)

    code_str = (request.POST.get('code') or request.GET.get('code') or '').strip().upper()
    try:
        base_fare = Decimal(str(request.POST.get('base_fare') or request.GET.get('base_fare') or '0'))
    except Exception:
        base_fare = Decimal('0.00')

    if not code_str:
        return JsonResponse({'valid': False, 'message': 'Please enter a promo code.'})

    promo = PromoCode.objects.filter(code=code_str).first()
    if not promo:
        return JsonResponse({'valid': False, 'message': f"Promo code '{code_str}' does not exist or is invalid."})

    taxes = round(base_fare * Decimal('0.12'), 2)
    service_fee = Decimal('49.00')
    gross_total = base_fare + taxes + service_fee

    user = request.user if request.user.is_authenticated else None
    is_valid, discount, msg = promo.is_valid_for_booking(gross_total, 'ALL', user)

    if not is_valid:
        return JsonResponse({'valid': False, 'code': promo.code, 'message': msg})

    new_total = max(Decimal('1.00'), gross_total - discount)

    return JsonResponse({
        'valid': True,
        'code': promo.code,
        'title': promo.title,
        'discount_amount': float(discount),
        'formatted_discount': f"-₹{discount:.2f}",
        'message': msg,
        'gross_total': float(gross_total),
        'new_total': float(new_total),
    })


def hotel_calculate_price(request):
    """
    AJAX endpoint for dynamic frontend price calculation:
    Takes: price_per_night, check_in, check_out, room_count, promo_code
    Returns: nights, base_fare, taxes, service_fee, discount, total
    """
    try:
        price_per_night = Decimal(str(request.GET.get('price_per_night', '0')))
        check_in_str = request.GET.get('check_in')
        check_out_str = request.GET.get('check_out')
        room_count = max(1, int(request.GET.get('rooms', 1)))
        promo_code_str = (request.GET.get('promo_code') or '').strip().upper()

        today = timezone.now().date()
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date() if check_in_str else today
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date() if check_out_str else check_in + timedelta(days=1)

        nights = max(1, (check_out - check_in).days)
        base_fare = price_per_night * Decimal(nights) * Decimal(room_count)
        taxes = round(base_fare * Decimal('0.12'), 2)
        service_fee = Decimal('49.00')
        gross_total = base_fare + taxes + service_fee

        discount = Decimal('0.00')
        promo_msg = ''
        if promo_code_str:
            promo = PromoCode.objects.filter(code=promo_code_str).first()
            if promo:
                is_valid, promo_disc, msg = promo.is_valid_for_booking(gross_total, 'ALL', request.user if request.user.is_authenticated else None)
                if is_valid:
                    discount = promo_disc
                    promo_msg = msg
                else:
                    promo_msg = msg

        total = max(Decimal('1.00'), gross_total - discount)

        return JsonResponse({
            'success': True,
            'nights': nights,
            'room_count': room_count,
            'price_per_night': float(price_per_night),
            'base_fare': float(base_fare),
            'taxes': float(taxes),
            'service_fee': float(service_fee),
            'discount': float(discount),
            'total': float(total),
            'promo_applied': discount > 0,
            'promo_message': promo_msg,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
