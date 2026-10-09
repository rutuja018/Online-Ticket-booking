from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden

from .models import StationRetiringRoom, RetiringRoomBooking
from railways.models import RailwayStation
from bookings.models import Booking

def retiring_room_index(request):
    """
    Search and landing page for Railway Station Retiring Rooms & Dormitories.
    """
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    stations = RailwayStation.objects.filter(is_active=True).order_by('city')

    station_query = request.GET.get('station', '').strip()
    slot_type = request.GET.get('slot_type', '24_HOURS')
    room_type_filter = request.GET.get('room_type', '')
    check_in_date_str = request.GET.get('check_in_date')
    pnr_param = request.GET.get('pnr', '').strip().upper()

    selected_station = None
    rooms = StationRetiringRoom.objects.filter(is_active=True).select_related('station')

    if station_query:
        # Search by code, city, or name
        stn = RailwayStation.objects.filter(
            code__iexact=station_query
        ).first() or RailwayStation.objects.filter(
            city__icontains=station_query
        ).first() or RailwayStation.objects.filter(
            name__icontains=station_query
        ).first()
        
        if stn:
            selected_station = stn
            rooms = rooms.filter(station=stn)
        else:
            messages.info(request, f"No retiring rooms found for '{station_query}'. Showing all stations.")

    if room_type_filter:
        rooms = rooms.filter(room_type=room_type_filter)

    # Sort rooms by price for selected slot
    if slot_type == '12_HOURS':
        rooms = rooms.order_by('price_12h')
    elif slot_type == '48_HOURS':
        rooms = rooms.order_by('price_48h')
    else:
        rooms = rooms.order_by('price_24h')

    # Pre-populate PNR data if provided
    if pnr_param and not station_query:
        b = Booking.objects.filter(pnr=pnr_param).first()
        if b and b.train_schedule:
            selected_station = b.train_schedule.destination_station
            rooms = StationRetiringRoom.objects.filter(station=selected_station, is_active=True)

    context = {
        'stations': stations,
        'selected_station': selected_station,
        'rooms': rooms,
        'slot_type': slot_type,
        'room_type_filter': room_type_filter,
        'station_query': station_query,
        'pnr_param': pnr_param,
        'today': today.isoformat(),
        'tomorrow': tomorrow.isoformat(),
    }
    return render(request, 'retiring_rooms/index.html', context)


def room_detail(request, room_id):
    """
    Room & Dormitory details with amenities, pricing tiers, and slot selection.
    """
    room = get_object_or_404(StationRetiringRoom.objects.select_related('station'), id=room_id, is_active=True)
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    slot_type = request.GET.get('slot_type', '24_HOURS')
    pnr_param = request.GET.get('pnr', '')

    context = {
        'room': room,
        'slot_type': slot_type,
        'pnr_param': pnr_param,
        'today': today.isoformat(),
        'tomorrow': tomorrow.isoformat(),
    }
    return render(request, 'retiring_rooms/detail.html', context)


def book_room(request, room_id):
    """
    Guest registration and pricing breakdown for retiring room reservation.
    """
    room = get_object_or_404(StationRetiringRoom.objects.select_related('station'), id=room_id, is_active=True)
    today = timezone.now().date()
    
    slot_type = request.GET.get('slot_type', '24_HOURS')
    check_in_str = request.GET.get('check_in_date') or today.isoformat()
    check_in_slot = request.GET.get('check_in_slot', '08:00 AM - 08:00 PM')
    pnr_param = request.GET.get('pnr', '').strip().upper()

    base_price = room.get_price_for_slot(slot_type)
    # GST: 12% for rooms > 1000, else 5%
    tax_rate = Decimal('0.12') if base_price >= Decimal('1000.00') else Decimal('0.05')
    taxes = round(base_price * tax_rate, 2)
    grand_total = base_price + taxes

    # Pre-fill guest data if logged in
    guest_name = ''
    guest_phone = ''
    guest_email = ''
    if request.user.is_authenticated:
        guest_name = request.user.get_full_name() or request.user.username
        guest_email = request.user.email
        if hasattr(request.user, 'profile') and request.user.profile.phone:
            guest_phone = request.user.profile.phone

    if pnr_param:
        b = Booking.objects.filter(pnr=pnr_param).first()
        if b:
            passengers = b.passengers.all()
            if passengers.exists():
                fp = passengers.first()
                guest_name = fp.full_name
                guest_phone = fp.phone or guest_phone

    context = {
        'room': room,
        'slot_type': slot_type,
        'check_in_date': check_in_str,
        'check_in_slot': check_in_slot,
        'base_price': base_price,
        'taxes': taxes,
        'grand_total': grand_total,
        'guest_name': guest_name,
        'guest_phone': guest_phone,
        'guest_email': guest_email,
        'pnr_param': pnr_param,
    }
    return render(request, 'retiring_rooms/book.html', context)


@transaction.atomic
def process_room_payment(request, room_id):
    """
    Simulates payment and confirms the Retiring Room / Dormitory booking.
    """
    if request.method != 'POST':
        return redirect('retiring_rooms:index')

    room = get_object_or_404(StationRetiringRoom.objects.select_related('station'), id=room_id, is_active=True)
    
    slot_type = request.POST.get('slot_type', '24_HOURS')
    check_in_date_str = request.POST.get('check_in_date')
    check_in_slot = request.POST.get('check_in_slot', '08:00 AM - 08:00 PM')
    
    guest_name = request.POST.get('guest_name', '').strip()
    guest_age = int(request.POST.get('guest_age', 30))
    guest_gender = request.POST.get('guest_gender', 'MALE')
    guest_phone = request.POST.get('guest_phone', '').strip()
    guest_email = request.POST.get('guest_email', '').strip()
    guest_id_type = request.POST.get('guest_id_type', 'AADHAAR')
    guest_id_number = request.POST.get('guest_id_number', '').strip()
    train_pnr = request.POST.get('train_pnr', '').strip().upper()
    payment_method = request.POST.get('payment_method', 'UPI')

    if not guest_name or not guest_phone or not guest_id_number:
        messages.error(request, "Please provide complete guest and ID verification details.")
        return redirect('retiring_rooms:book', room_id=room.id)

    try:
        from datetime import datetime
        check_in_date = datetime.strptime(check_in_date_str, '%Y-%m-%d').date()
    except Exception:
        check_in_date = timezone.now().date()

    # Calculate check-out date based on slot
    if slot_type == '48_HOURS':
        check_out_date = check_in_date + timedelta(days=2)
    elif slot_type == '24_HOURS':
        check_out_date = check_in_date + timedelta(days=1)
    else: # 12 hours
        check_out_date = check_in_date

    base_price = room.get_price_for_slot(slot_type)
    tax_rate = Decimal('0.12') if base_price >= Decimal('1000.00') else Decimal('0.05')
    taxes = round(base_price * tax_rate, 2)
    grand_total = base_price + taxes

    booking = RetiringRoomBooking.objects.create(
        user=request.user if request.user.is_authenticated else None,
        station=room.station,
        room=room,
        slot_type=slot_type,
        check_in_date=check_in_date,
        check_in_time_slot=check_in_slot,
        check_out_date=check_out_date,
        guest_count=1,
        guest_name=guest_name,
        guest_age=guest_age,
        guest_gender=guest_gender,
        guest_phone=guest_phone,
        guest_email=guest_email,
        guest_id_type=guest_id_type,
        guest_id_number=guest_id_number,
        train_pnr=train_pnr,
        base_amount=base_price,
        taxes=taxes,
        total_amount=grand_total,
        booking_status='CONFIRMED',
        payment_status='SUCCESS',
        payment_method=payment_method,
    )

    messages.success(request, f"Station Retiring Room confirmed! Reference #{booking.booking_ref}. Your digital station stay pass is ready.")
    return redirect('retiring_rooms:booking_pass', booking_ref=booking.booking_ref)


def booking_pass(request, booking_ref):
    """
    High-resolution printable digital Retiring Room Pass with Station details & QR barcode.
    """
    booking = get_object_or_404(
        RetiringRoomBooking.objects.select_related('station', 'room', 'user'),
        booking_ref=booking_ref
    )
    return render(request, 'retiring_rooms/pass.html', {'booking': booking})


def cancel_booking(request, booking_ref):
    """
    1-Click automated cancellation for station room bookings.
    """
    booking = get_object_or_404(RetiringRoomBooking, booking_ref=booking_ref)
    
    if request.user.is_authenticated and booking.user and booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Not authorized to cancel this booking.")

    if booking.booking_status == 'CANCELLED':
        messages.info(request, "This booking is already cancelled.")
        return redirect('retiring_rooms:booking_pass', booking_ref=booking.booking_ref)

    # 90% refund policy
    refund = round(booking.base_amount * Decimal('0.90'), 2)
    booking.booking_status = 'CANCELLED'
    booking.payment_status = 'REFUNDED'
    booking.cancelled_at = timezone.now()
    booking.refund_amount = refund
    booking.save()

    messages.success(request, f"Retiring Room Booking #{booking.booking_ref} cancelled successfully. Refund of ₹{refund} initiated.")
    return redirect('retiring_rooms:booking_pass', booking_ref=booking.booking_ref)
