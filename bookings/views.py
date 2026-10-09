import calendar
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse

from .models import Booking, Passenger, PromoCode
from railways.models import TrainSchedule, TrainSeat
from airlines.models import FlightSchedule, FlightSeat
from buses.models import BusSchedule, BusSeat
from hotels.models import HotelBooking
from retiring_rooms.models import RetiringRoomBooking
from food_catering.models import FoodOrder

def validate_promo_code(request):
    """
    AJAX endpoint to validate promo code in real-time.
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'valid': False, 'message': 'Invalid request method.'}, status=405)

    code_str = (request.POST.get('code') or request.GET.get('code') or request.POST.get('promo_code') or '').strip().upper()
    transport_type = (request.POST.get('transport_type') or request.GET.get('transport_type') or 'FLIGHT').strip().upper()
    
    try:
        base_fare = Decimal(str(request.POST.get('base_fare') or request.GET.get('base_fare') or '0'))
    except Exception:
        base_fare = Decimal('0.00')

    try:
        seat_count = int(request.POST.get('seat_count') or request.GET.get('seat_count') or 1)
    except Exception:
        seat_count = 1

    if not code_str:
        return JsonResponse({'valid': False, 'message': 'Please enter a promo code.'})

    promo = PromoCode.objects.filter(code=code_str).first()
    if not promo:
        return JsonResponse({
            'valid': False,
            'message': f"Promo code '{code_str}' is invalid or does not exist."
        })

    # Estimate gross booking amount
    tax_rate = Decimal('0.12') if transport_type == 'FLIGHT' else Decimal('0.05')
    base_total = base_fare * Decimal(max(1, seat_count))
    taxes = round(base_total * tax_rate, 2)
    service_fee = Decimal('49.00')
    gross_total = base_total + taxes + service_fee

    user = request.user if request.user.is_authenticated else None
    is_valid, discount_amount, msg = promo.is_valid_for_booking(gross_total, transport_type, user)

    if not is_valid:
        return JsonResponse({
            'valid': False,
            'code': promo.code,
            'message': msg
        })

    new_total = max(Decimal('1.00'), gross_total - discount_amount)

    return JsonResponse({
        'valid': True,
        'code': promo.code,
        'title': promo.title,
        'discount_amount': float(discount_amount),
        'formatted_discount': f"-₹{discount_amount:.2f}",
        'message': msg,
        'gross_total': float(gross_total),
        'new_total': float(new_total),
    })

@login_required
def create_booking(request):
    """
    Handles booking submission from seat selection and passenger input.
    Uses select_for_update() inside atomic transaction to ensure concurrency safety.
    """
    if request.method != 'POST':
        return redirect('core:home')

    transport_type = request.POST.get('transport_type')
    schedule_id = request.POST.get('schedule_id')
    travel_class = request.POST.get('travel_class', 'STANDARD')
    selected_seats_str = request.POST.get('selected_seats', '').strip()

    if not selected_seats_str:
        messages.error(request, "Please select at least one seat to proceed.")
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))

    seat_numbers = [s.strip() for s in selected_seats_str.split(',') if s.strip()]
    passenger_count = len(seat_numbers)

    try:
        with transaction.atomic():
            train_schedule = None
            flight_schedule = None
            bus_schedule = None
            base_seat_fare = Decimal('0.00')
            service_title = ""
            source_loc = ""
            dest_loc = ""
            journey_date = timezone.now().date()
            dep_time = ""
            arr_time = ""
            duration_txt = ""

            # 1. Train Booking Processing
            if transport_type == 'TRAIN':
                train_schedule = TrainSchedule.objects.select_for_update().get(id=schedule_id, is_active=True)
                service_title = f"{train_schedule.train.name} ({train_schedule.train.train_number})"
                source_loc = f"{train_schedule.source_station.name} ({train_schedule.source_station.code})"
                dest_loc = f"{train_schedule.destination_station.name} ({train_schedule.destination_station.code})"
                journey_date = train_schedule.journey_date
                dep_time = train_schedule.departure_time.strftime('%H:%M')
                arr_time = train_schedule.arrival_time.strftime('%H:%M')
                duration_txt = train_schedule.formatted_duration
                base_seat_fare = train_schedule.get_fare_for_class(travel_class)

                # Check seat availability and lock
                for s_str in seat_numbers:
                    coach_parts = s_str.split('-')
                    if len(coach_parts) == 2:
                        seat_obj = TrainSeat.objects.select_for_update().filter(
                            schedule=train_schedule, coach=coach_parts[0].strip(), seat_number=coach_parts[1].strip()
                        ).first()
                    else:
                        seat_obj = TrainSeat.objects.select_for_update().filter(
                            schedule=train_schedule, seat_number=s_str
                        ).first()

                    if not seat_obj or seat_obj.is_booked:
                        messages.error(request, f"Seat {s_str} is already occupied or unavailable. Please choose another seat.")
                        return redirect('railways:seat_select', schedule_id=schedule_id)

            # 2. Flight Booking Processing
            elif transport_type == 'FLIGHT':
                flight_schedule = FlightSchedule.objects.select_for_update().get(id=schedule_id, is_active=True)
                service_title = f"{flight_schedule.flight.airline.name} {flight_schedule.flight.flight_number}"
                source_loc = f"{flight_schedule.origin_airport.name} ({flight_schedule.origin_airport.code})"
                dest_loc = f"{flight_schedule.destination_airport.name} ({flight_schedule.destination_airport.code})"
                journey_date = flight_schedule.departure_datetime.date()
                dep_time = flight_schedule.departure_datetime.strftime('%H:%M')
                arr_time = flight_schedule.arrival_datetime.strftime('%H:%M')
                duration_txt = flight_schedule.formatted_duration
                base_seat_fare = flight_schedule.get_fare_for_class(travel_class)

                for s_str in seat_numbers:
                    seat_obj = FlightSeat.objects.select_for_update().filter(
                        schedule=flight_schedule, seat_number=s_str
                    ).first()
                    if not seat_obj or seat_obj.is_booked:
                        messages.error(request, f"Seat {s_str} is already occupied. Please select an available seat.")
                        return redirect('airlines:seat_select', schedule_id=schedule_id)

            # 3. Bus Booking Processing
            elif transport_type == 'BUS':
                bus_schedule = BusSchedule.objects.select_for_update().get(id=schedule_id, is_active=True)
                service_title = f"{bus_schedule.bus.operator.name} ({bus_schedule.bus.bus_number})"
                source_loc = bus_schedule.route.source_city
                dest_loc = bus_schedule.route.destination_city
                journey_date = bus_schedule.journey_date
                dep_time = bus_schedule.departure_time.strftime('%H:%M')
                arr_time = bus_schedule.arrival_time.strftime('%H:%M')
                duration_txt = bus_schedule.formatted_duration
                base_seat_fare = bus_schedule.base_fare

                for s_str in seat_numbers:
                    seat_obj = BusSeat.objects.select_for_update().filter(
                        schedule=bus_schedule, seat_number=s_str
                    ).first()
                    if not seat_obj or seat_obj.is_booked:
                        messages.error(request, f"Seat {s_str} is already occupied. Please select an available seat.")
                        return redirect('buses:seat_select', schedule_id=schedule_id)

            # Calculate Pricing Breakdown
            base_total = base_seat_fare * Decimal(passenger_count)
            tax_rate = Decimal('0.12') if transport_type == 'FLIGHT' else Decimal('0.05')
            taxes = round(base_total * tax_rate, 2)
            service_fee = Decimal('49.00')
            gross_total = base_total + taxes + service_fee

            # Promo Code Validation & Discount (Strict Server-Side Enforcement)
            discount = Decimal('0.00')
            applied_promo = None
            promo_code_str = request.POST.get('promo_code', '').strip().upper()

            if promo_code_str:
                promo_obj = PromoCode.objects.filter(code=promo_code_str).first()
                if promo_obj:
                    is_valid, promo_discount, promo_msg = promo_obj.is_valid_for_booking(
                        gross_total, transport_type, request.user
                    )
                    if is_valid:
                        applied_promo = promo_obj
                        discount = promo_discount
                    else:
                        messages.warning(request, f"Promo code '{promo_code_str}' could not be applied: {promo_msg}")
                else:
                    messages.warning(request, f"Promo code '{promo_code_str}' is invalid or expired.")

            total_amount = max(Decimal('1.00'), gross_total - discount)

            # Create Booking Record in PENDING state
            booking = Booking.objects.create(
                user=request.user,
                transport_type=transport_type,
                train_schedule=train_schedule,
                flight_schedule=flight_schedule,
                bus_schedule=bus_schedule,
                service_title=service_title,
                travel_class=travel_class,
                source_location=source_loc,
                destination_location=dest_loc,
                journey_date=journey_date,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration_text=duration_txt,
                passenger_count=passenger_count,
                allocated_seats=selected_seats_str,
                base_fare=base_total,
                taxes=taxes,
                service_fee=service_fee,
                discount=discount,
                promo_code=applied_promo.code if applied_promo else (promo_code_str if discount > 0 else None),
                promo_code_obj=applied_promo,
                total_amount=total_amount,
                booking_status='PENDING',
                payment_status='PENDING',
            )

            # Save Passenger Information
            for i in range(1, passenger_count + 1):
                full_name = request.POST.get(f'passenger_{i}_name', f'Passenger {i}').strip()
                age = int(request.POST.get(f'passenger_{i}_age', 25))
                gender = request.POST.get(f'passenger_{i}_gender', 'MALE')
                phone = request.POST.get(f'passenger_{i}_phone', request.user.profile.phone or '')
                email = request.POST.get(f'passenger_{i}_email', request.user.email or '')
                id_type = request.POST.get(f'passenger_{i}_id_type', 'AADHAAR')
                id_number = request.POST.get(f'passenger_{i}_id_number', '123456789012')
                assigned_seat = seat_numbers[i - 1] if i - 1 < len(seat_numbers) else f"Seat {i}"
                berth_pref = request.POST.get(f'passenger_{i}_berth_pref', '')

                Passenger.objects.create(
                    booking=booking,
                    full_name=full_name,
                    age=age,
                    gender=gender,
                    phone=phone,
                    email=email,
                    id_type=id_type,
                    id_number=id_number,
                    seat_number=assigned_seat,
                    berth_preference=berth_pref,
                )

            return redirect('payments:process_payment', booking_id=booking.id)

    except Exception as e:
        messages.error(request, f"An error occurred while creating your reservation: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))


@login_required
def booking_review(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('user').prefetch_related('passengers'),
        id=booking_id
    )
    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have access to view this booking.")

    return render(request, 'bookings/review.html', {'booking': booking})


@login_required
def booking_ticket(request, pnr):
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'payment').prefetch_related('passengers'),
        pnr=pnr
    )
    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to access this ticket.")

    can_cancel, reason_msg = booking.can_be_cancelled()

    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'reason_msg': reason_msg,
    }
    return render(request, 'bookings/ticket.html', context)


@login_required
def booking_history(request):
    transport_filter = request.GET.get('transport', '').strip()
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

    user_all_bookings = Booking.objects.filter(user=request.user)
    user_all_hotels = HotelBooking.objects.filter(user=request.user).select_related('hotel', 'room')
    user_all_rooms = RetiringRoomBooking.objects.filter(user=request.user).select_related('station', 'room')
    user_all_food = FoodOrder.objects.filter(user=request.user).select_related('restaurant', 'delivery_station').prefetch_related('items')

    total_user_bookings = (
        user_all_bookings.count() +
        user_all_hotels.count() +
        user_all_rooms.count() +
        user_all_food.count()
    )

    bookings = user_all_bookings.select_related('payment').prefetch_related('passengers')
    hotel_bookings = user_all_hotels
    retiring_room_bookings = user_all_rooms
    food_orders = user_all_food

    if transport_filter:
        if transport_filter == 'HOTEL':
            bookings = Booking.objects.none()
            retiring_room_bookings = RetiringRoomBooking.objects.none()
            food_orders = FoodOrder.objects.none()
        elif transport_filter in ['RETIRING_ROOM', 'ROOM']:
            bookings = Booking.objects.none()
            hotel_bookings = HotelBooking.objects.none()
            food_orders = FoodOrder.objects.none()
        elif transport_filter in ['FOOD', 'MEAL', 'FOOD_ORDER']:
            bookings = Booking.objects.none()
            hotel_bookings = HotelBooking.objects.none()
            retiring_room_bookings = RetiringRoomBooking.objects.none()
        else:
            bookings = bookings.filter(transport_type=transport_filter)
            hotel_bookings = HotelBooking.objects.none()
            retiring_room_bookings = RetiringRoomBooking.objects.none()
            food_orders = FoodOrder.objects.none()

    if status_filter:
        if status_filter == 'CANCELLED':
            bookings = bookings.filter(booking_status__in=['CANCELLED', 'REFUNDED'])
            hotel_bookings = hotel_bookings.filter(booking_status__in=['CANCELLED', 'REFUNDED'])
            retiring_room_bookings = retiring_room_bookings.filter(booking_status__in=['CANCELLED', 'REFUNDED'])
            food_orders = food_orders.filter(status__in=['CANCELLED', 'REFUNDED'])
        elif status_filter == 'CONFIRMED':
            bookings = bookings.filter(booking_status='CONFIRMED')
            hotel_bookings = hotel_bookings.filter(booking_status='CONFIRMED')
            retiring_room_bookings = retiring_room_bookings.filter(booking_status__in=['CONFIRMED', 'CHECKED_IN', 'COMPLETED'])
            food_orders = food_orders.filter(status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED'])
        elif status_filter == 'PENDING':
            bookings = bookings.filter(booking_status='PENDING')
            hotel_bookings = hotel_bookings.filter(booking_status='PENDING')
            retiring_room_bookings = retiring_room_bookings.filter(payment_status='PENDING')
            food_orders = food_orders.filter(payment_status='PENDING')
        else:
            bookings = bookings.filter(booking_status=status_filter)
            hotel_bookings = hotel_bookings.filter(booking_status=status_filter)
            retiring_room_bookings = retiring_room_bookings.filter(booking_status=status_filter)
            food_orders = food_orders.filter(status=status_filter)

    if search_query:
        bookings = bookings.filter(
            Q(pnr__icontains=search_query) |
            Q(service_title__icontains=search_query) |
            Q(source_location__icontains=search_query) |
            Q(destination_location__icontains=search_query) |
            Q(passengers__full_name__icontains=search_query) |
            Q(allocated_seats__icontains=search_query) |
            Q(travel_class__icontains=search_query)
        ).distinct()

        hotel_bookings = hotel_bookings.filter(
            Q(booking_reference__icontains=search_query) |
            Q(hotel__name__icontains=search_query) |
            Q(hotel__city__icontains=search_query) |
            Q(primary_guest_name__icontains=search_query) |
            Q(room__room_type__icontains=search_query)
        ).distinct()

        retiring_room_bookings = retiring_room_bookings.filter(
            Q(booking_ref__icontains=search_query) |
            Q(station__name__icontains=search_query) |
            Q(station__code__icontains=search_query) |
            Q(station__city__icontains=search_query) |
            Q(guest_name__icontains=search_query) |
            Q(train_pnr__icontains=search_query) |
            Q(room__room_or_bed_no__icontains=search_query) |
            Q(room__room_type__icontains=search_query)
        ).distinct()

        food_orders = food_orders.filter(
            Q(order_ref__icontains=search_query) |
            Q(pnr__icontains=search_query) |
            Q(train_number__icontains=search_query) |
            Q(train_name__icontains=search_query) |
            Q(delivery_station__name__icontains=search_query) |
            Q(delivery_station__code__icontains=search_query) |
            Q(restaurant__name__icontains=search_query) |
            Q(passenger_name__icontains=search_query) |
            Q(items__item_name__icontains=search_query)
        ).distinct()

    # Counts for filter tab badges
    counts = {
        'all': total_user_bookings,
        'train': user_all_bookings.filter(transport_type='TRAIN').count(),
        'flight': user_all_bookings.filter(transport_type='FLIGHT').count(),
        'bus': user_all_bookings.filter(transport_type='BUS').count(),
        'hotel': user_all_hotels.count(),
        'retiring_room': user_all_rooms.count(),
        'food': user_all_food.count(),
        'confirmed': (
            user_all_bookings.filter(booking_status='CONFIRMED').count() +
            user_all_hotels.filter(booking_status='CONFIRMED').count() +
            user_all_rooms.filter(booking_status__in=['CONFIRMED', 'CHECKED_IN', 'COMPLETED']).count() +
            user_all_food.filter(status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED']).count()
        ),
        'pending': (
            user_all_bookings.filter(booking_status='PENDING').count() +
            user_all_hotels.filter(booking_status='PENDING').count() +
            user_all_rooms.filter(payment_status='PENDING').count() +
            user_all_food.filter(payment_status='PENDING').count()
        ),
        'cancelled': (
            user_all_bookings.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count() +
            user_all_hotels.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count() +
            user_all_rooms.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count() +
            user_all_food.filter(status__in=['CANCELLED', 'REFUNDED']).count()
        ),
    }

    context = {
        'bookings': bookings,
        'hotel_bookings': hotel_bookings,
        'retiring_room_bookings': retiring_room_bookings,
        'food_orders': food_orders,
        'selected_transport': transport_filter,
        'selected_status': status_filter,
        'search_query': search_query,
        'total_user_bookings': total_user_bookings,
        'counts': counts,
        'has_filters': bool(transport_filter or status_filter or search_query),
    }
    return render(request, 'bookings/history.html', context)


@login_required
def booking_cancel(request, pnr):
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'payment').prefetch_related('passengers'),
        pnr=pnr
    )
    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to cancel this booking.")

    can_cancel, reason_msg = booking.can_be_cancelled()
    estimated_refund = booking.calculate_refund() if can_cancel else Decimal('0.00')

    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', 'User requested cancellation')
        success, message = booking.cancel_and_release_seats(reason=cancellation_reason)
        if success:
            messages.success(request, message)
            return redirect('bookings:ticket', pnr=booking.pnr)
        else:
            messages.error(request, message)

    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'reason_msg': reason_msg,
        'estimated_refund': estimated_refund,
    }
    return render(request, 'bookings/cancel_confirm.html', context)


def _extract_user_calendar_events(user, start_date=None, end_date=None, transport_filter=None, status_filter=None):
    """
    Extracts unified event objects across all bookings (Trains, Flights, Buses, Hotels, Retiring Rooms, Food)
    for calendar rendering and agenda timelines.
    """
    events = []
    
    # 1. Transport Bookings (Train, Flight, Bus)
    bookings_qs = Booking.objects.filter(user=user).select_related('train_schedule', 'flight_schedule', 'bus_schedule').prefetch_related('passengers')
    if start_date:
        bookings_qs = bookings_qs.filter(journey_date__gte=start_date)
    if end_date:
        bookings_qs = bookings_qs.filter(journey_date__lte=end_date)
    if transport_filter and transport_filter in ['TRAIN', 'FLIGHT', 'BUS']:
        bookings_qs = bookings_qs.filter(transport_type=transport_filter)
    elif transport_filter and transport_filter not in ['ALL', '']:
        bookings_qs = Booking.objects.none()

    if status_filter:
        if status_filter == 'CONFIRMED':
            bookings_qs = bookings_qs.filter(booking_status='CONFIRMED')
        elif status_filter == 'PENDING':
            bookings_qs = bookings_qs.filter(booking_status='PENDING')
        elif status_filter == 'CANCELLED':
            bookings_qs = bookings_qs.filter(booking_status__in=['CANCELLED', 'REFUNDED'])

    badge_map = {
        'TRAIN': ('cal-event-train', 'fa-solid fa-train', '#ea580c'),
        'FLIGHT': ('cal-event-flight', 'fa-solid fa-plane-departure', '#0284c7'),
        'BUS': ('cal-event-bus', 'fa-solid fa-bus', '#059669'),
    }

    for b in bookings_qs:
        badge_class, icon, theme_color = badge_map.get(b.transport_type, ('cal-event-train', 'fa-solid fa-ticket', '#ea580c'))
        is_canc = b.booking_status in ['CANCELLED', 'REFUNDED']
        passenger_names = [p.full_name for p in b.passengers.all()]

        events.append({
            'id': f"booking-{b.id}",
            'type': b.transport_type,
            'type_display': b.get_transport_type_display(),
            'title': b.service_title,
            'ref': b.pnr,
            'date': b.journey_date.isoformat(),
            'end_date': b.journey_date.isoformat(),
            'time': b.departure_time or '--:--',
            'arrival_time': b.arrival_time or '--:--',
            'duration': b.duration_text or '',
            'origin': b.source_location,
            'destination': b.destination_location,
            'route_display': f"{b.source_location} → {b.destination_location}",
            'seats': b.allocated_seats or 'Assigned upon confirmation',
            'travel_class': b.travel_class,
            'passengers': passenger_names if passenger_names else [user.get_full_name() or user.username],
            'passenger_count': b.passenger_count,
            'fare': float(b.total_amount),
            'status': b.booking_status,
            'status_display': b.get_booking_status_display(),
            'is_cancelled': is_canc,
            'is_upcoming': b.is_upcoming,
            'url': f"/bookings/{b.pnr}/ticket/",
            'cancel_url': f"/bookings/{b.pnr}/cancel/" if b.is_cancellable else None,
            'badge_class': badge_class if not is_canc else 'cal-event-cancelled',
            'icon': icon,
            'theme_color': theme_color,
        })

    # 2. Hotel Bookings
    if not transport_filter or transport_filter in ['HOTEL', 'ALL']:
        hotel_qs = HotelBooking.objects.filter(user=user).select_related('hotel', 'room')
        if start_date:
            hotel_qs = hotel_qs.filter(check_in_date__gte=start_date)
        if end_date:
            hotel_qs = hotel_qs.filter(check_in_date__lte=end_date)
        if status_filter:
            if status_filter == 'CONFIRMED':
                hotel_qs = hotel_qs.filter(booking_status='CONFIRMED')
            elif status_filter == 'PENDING':
                hotel_qs = hotel_qs.filter(booking_status='PENDING')
            elif status_filter == 'CANCELLED':
                hotel_qs = hotel_qs.filter(booking_status__in=['CANCELLED', 'REFUNDED'])

        for hb in hotel_qs:
            is_canc = hb.booking_status in ['CANCELLED', 'REFUNDED']
            events.append({
                'id': f"hotel-{hb.id}",
                'type': 'HOTEL',
                'type_display': 'Hotel Stay',
                'title': hb.hotel.name,
                'ref': hb.booking_reference,
                'date': hb.check_in_date.isoformat(),
                'end_date': hb.check_out_date.isoformat(),
                'time': 'Check-in: 12:00 PM',
                'arrival_time': f"Check-out: {hb.check_out_date.strftime('%d %b')}",
                'duration': f"{hb.nights} Night(s)",
                'origin': f"{hb.hotel.city} ({hb.hotel.name})",
                'destination': f"{hb.room.room_type} ({hb.room_count} Room)",
                'route_display': f"{hb.hotel.name}, {hb.hotel.city}",
                'seats': f"{hb.room_count} Room(s) &bull; {hb.guest_count} Guests",
                'travel_class': hb.room.room_type,
                'passengers': [hb.primary_guest_name or user.get_full_name() or user.username],
                'passenger_count': hb.guest_count,
                'fare': float(hb.total_amount),
                'status': hb.booking_status,
                'status_display': hb.get_booking_status_display(),
                'is_cancelled': is_canc,
                'is_upcoming': hb.is_upcoming,
                'url': f"/hotels/confirmation/{hb.booking_reference}/",
                'cancel_url': f"/hotels/cancel/{hb.booking_reference}/" if hb.is_cancellable else None,
                'badge_class': 'cal-event-hotel' if not is_canc else 'cal-event-cancelled',
                'icon': 'fa-solid fa-hotel',
                'theme_color': '#9333ea',
            })

    # 3. Retiring Rooms
    if not transport_filter or transport_filter in ['RETIRING_ROOM', 'ROOM', 'ALL']:
        room_qs = RetiringRoomBooking.objects.filter(user=user).select_related('station', 'room')
        if start_date:
            room_qs = room_qs.filter(check_in_date__gte=start_date)
        if end_date:
            room_qs = room_qs.filter(check_in_date__lte=end_date)
        if status_filter:
            if status_filter == 'CONFIRMED':
                room_qs = room_qs.filter(booking_status__in=['CONFIRMED', 'CHECKED_IN'])
            elif status_filter == 'PENDING':
                room_qs = room_qs.filter(payment_status='PENDING')
            elif status_filter == 'CANCELLED':
                room_qs = room_qs.filter(booking_status__in=['CANCELLED', 'REFUNDED'])

        for rb in room_qs:
            is_canc = rb.booking_status in ['CANCELLED', 'REFUNDED']
            events.append({
                'id': f"room-{rb.id}",
                'type': 'RETIRING_ROOM',
                'type_display': 'Retiring Room',
                'title': f"Retiring Room at {rb.station.name}",
                'ref': rb.booking_ref,
                'date': rb.check_in_date.isoformat(),
                'end_date': rb.check_out_date.isoformat(),
                'time': f"Slot: {rb.slot_duration_hours}h",
                'arrival_time': f"Out: {rb.check_out_date.strftime('%d %b')}",
                'duration': f"{rb.slot_duration_hours} Hours",
                'origin': f"{rb.station.city} ({rb.station.code})",
                'destination': f"Room/Bed #{rb.room.room_or_bed_no} ({rb.room.room_type})",
                'route_display': f"Station: {rb.station.name} ({rb.station.code})",
                'seats': f"Bed #{rb.room.room_or_bed_no}",
                'travel_class': rb.room.room_type,
                'passengers': [rb.guest_name or user.get_full_name() or user.username],
                'passenger_count': 1,
                'fare': float(rb.total_amount),
                'status': rb.booking_status,
                'status_display': rb.get_booking_status_display(),
                'is_cancelled': is_canc,
                'is_upcoming': rb.check_in_date >= timezone.now().date() and not is_canc,
                'url': f"/retiring-rooms/pass/{rb.booking_ref}/",
                'cancel_url': f"/retiring-rooms/cancel/{rb.booking_ref}/" if rb.is_cancellable else None,
                'badge_class': 'cal-event-room' if not is_canc else 'cal-event-cancelled',
                'icon': 'fa-solid fa-bed',
                'theme_color': '#0f766e',
            })

    # 4. Food Orders
    if not transport_filter or transport_filter in ['FOOD', 'MEAL', 'ALL']:
        food_qs = FoodOrder.objects.filter(user=user).select_related('restaurant', 'delivery_station')
        if start_date:
            food_qs = food_qs.filter(delivery_date__gte=start_date)
        if end_date:
            food_qs = food_qs.filter(delivery_date__lte=end_date)
        if status_filter:
            if status_filter == 'CONFIRMED':
                food_qs = food_qs.filter(status__in=['CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED'])
            elif status_filter == 'PENDING':
                food_qs = food_qs.filter(payment_status='PENDING')
            elif status_filter == 'CANCELLED':
                food_qs = food_qs.filter(status__in=['CANCELLED', 'REFUNDED'])

        for fo in food_qs:
            is_canc = fo.status in ['CANCELLED', 'REFUNDED']
            events.append({
                'id': f"food-{fo.id}",
                'type': 'FOOD',
                'type_display': 'Food in Train',
                'title': f"Meal: {fo.restaurant.name}",
                'ref': fo.order_ref,
                'date': fo.delivery_date.isoformat(),
                'end_date': fo.delivery_date.isoformat(),
                'time': fo.delivery_time_slot or 'Meal Time',
                'arrival_time': '',
                'duration': '',
                'origin': f"Train {fo.train_number} - {fo.delivery_station.name}",
                'destination': f"Seat {fo.coach_number}/{fo.berth_seat_number}",
                'route_display': f"Delivery at {fo.delivery_station.name} (Train {fo.train_number})",
                'seats': f"{fo.coach_number}-{fo.berth_seat_number}",
                'travel_class': 'Catering',
                'passengers': [fo.passenger_name or user.get_full_name() or user.username],
                'passenger_count': 1,
                'fare': float(fo.total_amount),
                'status': fo.status,
                'status_display': fo.get_status_display(),
                'is_cancelled': is_canc,
                'is_upcoming': fo.delivery_date >= timezone.now().date() and not is_canc,
                'url': f"/food/track/{fo.order_ref}/",
                'cancel_url': f"/food/cancel/{fo.order_ref}/" if fo.can_be_cancelled else None,
                'badge_class': 'cal-event-food' if not is_canc else 'cal-event-cancelled',
                'icon': 'fa-solid fa-utensils',
                'theme_color': '#d97706',
            })

    # Sort events by date and time
    events.sort(key=lambda x: (x['date'], x['time']))
    return events


@login_required
def booking_calendar(request):
    """
    Dedicated Interactive Travel Itinerary Calendar View.
    Shows monthly, weekly, and timeline view of all journeys, hotel stays, and activities.
    """
    user = request.user
    today = timezone.now().date()
    
    # Load all user events
    all_events = _extract_user_calendar_events(user)
    
    # Pre-calculated summary counts
    upcoming_events = [e for e in all_events if e['is_upcoming']]
    confirmed_count = len([e for e in all_events if not e['is_cancelled']])
    cancelled_count = len([e for e in all_events if e['is_cancelled']])

    # Find the next upcoming event
    next_event = upcoming_events[0] if upcoming_events else None

    # Categories breakdown
    counts = {
        'total': len(all_events),
        'upcoming': len(upcoming_events),
        'train': len([e for e in all_events if e['type'] == 'TRAIN']),
        'flight': len([e for e in all_events if e['type'] == 'FLIGHT']),
        'bus': len([e for e in all_events if e['type'] == 'BUS']),
        'hotel': len([e for e in all_events if e['type'] == 'HOTEL']),
        'retiring_room': len([e for e in all_events if e['type'] == 'RETIRING_ROOM']),
        'food': len([e for e in all_events if e['type'] == 'FOOD']),
    }

    context = {
        'today_iso': today.isoformat(),
        'today_year': today.year,
        'today_month': today.month,
        'today_day': today.day,
        'events_json': json.dumps(all_events),
        'next_event': next_event,
        'counts': counts,
        'upcoming_count': len(upcoming_events),
        'confirmed_count': confirmed_count,
        'cancelled_count': cancelled_count,
    }
    return render(request, 'bookings/calendar.html', context)


@login_required
def booking_calendar_events_api(request):
    """
    AJAX endpoint to return JSON events for any requested date range or filters.
    """
    year_str = request.GET.get('year')
    month_str = request.GET.get('month')
    transport_filter = request.GET.get('transport', '').strip()
    status_filter = request.GET.get('status', '').strip()

    start_date = None
    end_date = None

    if year_str and month_str:
        try:
            year = int(year_str)
            month = int(month_str)
            _, num_days = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, num_days)
        except Exception:
            pass

    events = _extract_user_calendar_events(
        user=request.user,
        start_date=start_date,
        end_date=end_date,
        transport_filter=transport_filter,
        status_filter=status_filter
    )

    return JsonResponse({'success': True, 'events': events})


@login_required
def export_calendar_ics(request):
    """
    Exports the user's travel itinerary into standard RFC 5545 iCalendar (.ics) format
    so it can be imported into Apple Calendar, Google Calendar, Outlook, etc.
    """
    user = request.user
    events = _extract_user_calendar_events(user, status_filter='CONFIRMED')

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RailAway Travel Portal//Itinerary Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:RailAway Itinerary ({user.username})",
        "X-WR-TIMEZONE:Asia/Kolkata",
    ]

    now_utc_str = timezone.now().strftime('%Y%m%dT%H%M%SZ')

    for ev in events:
        # Date and time parsing
        try:
            ev_date = datetime.strptime(ev['date'], '%Y-%m-%d').date()
            dtstart = f"{ev_date.strftime('%Y%m%d')}T090000"
            if ev.get('time') and ":" in ev['time']:
                t_parts = ev['time'].split(":")
                hour = int(t_parts[0])
                minute = int(t_parts[1][:2])
                dtstart = f"{ev_date.strftime('%Y%m%d')}T{hour:02d}{minute:02d}00"
            
            # 2 hour duration default or end_date for hotel
            if ev['type'] == 'HOTEL' and ev.get('end_date'):
                end_d = datetime.strptime(ev['end_date'], '%Y-%m-%d').date()
                dtend = f"{end_d.strftime('%Y%m%d')}T120000"
            else:
                dtend = f"{ev_date.strftime('%Y%m%d')}T210000"
        except Exception:
            dtstart = f"{timezone.now().strftime('%Y%m%d')}T090000"
            dtend = f"{timezone.now().strftime('%Y%m%d')}T120000"

        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:railaway-{ev['id']}@railaway.in",
            f"DTSTAMP:{now_utc_str}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{ev['type_display']}: {ev['title']} ({ev['ref']})",
            f"LOCATION:{ev.get('origin', '')} to {ev.get('destination', '')}",
            f"DESCRIPTION:Booking Ref: {ev['ref']}\\nRoute: {ev.get('route_display', '')}\\nSeats: {ev.get('seats', '')}\\nStatus: {ev['status_display']}",
            "STATUS:CONFIRMED",
            "BEGIN:VALARM",
            "TRIGGER:-PT2H",
            "ACTION:DISPLAY",
            f"DESCRIPTION:Upcoming Departure Reminder: {ev['title']}",
            "END:VALARM",
            "END:VEVENT",
        ])

    ics_lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(ics_lines)

    response = HttpResponse(ics_content, content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="RailAway_Itinerary_{user.username}.ics"'
    return response
