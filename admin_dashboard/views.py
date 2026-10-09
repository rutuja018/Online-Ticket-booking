from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from bookings.models import Booking
from payments.models import Payment
from railways.models import Train, TrainSchedule, RailwayStation
from airlines.models import Flight, FlightSchedule, Airport, Airline
from buses.models import Bus, BusSchedule, BusOperator, BusRoute
from hotels.models import Hotel, Room, HotelBooking

def is_staff_or_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN'


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def admin_home(request):
    """
    Administrator analytics hub with KPIs, Revenue, Transport breakdown, and recent orders.
    """
    total_users = User.objects.count()
    all_bookings = Booking.objects.all()
    all_hotel_bookings = HotelBooking.objects.all()
    
    total_bookings = all_bookings.count() + all_hotel_bookings.count()
    confirmed_bookings = all_bookings.filter(booking_status='CONFIRMED').count() + all_hotel_bookings.filter(booking_status='CONFIRMED').count()
    cancelled_bookings = all_bookings.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count() + all_hotel_bookings.filter(booking_status__in=['CANCELLED', 'REFUNDED']).count()

    # Revenue
    transport_revenue = all_bookings.filter(
        booking_status='CONFIRMED', payment_status='SUCCESS'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    hotel_revenue = all_hotel_bookings.filter(
        booking_status='CONFIRMED', payment_status='SUCCESS'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    total_revenue = transport_revenue + hotel_revenue

    refund_total = (
        all_bookings.filter(booking_status='CANCELLED').aggregate(total=Sum('refund_amount'))['total'] or Decimal('0.00')
    ) + (
        all_hotel_bookings.filter(booking_status='CANCELLED').aggregate(total=Sum('refund_amount'))['total'] or Decimal('0.00')
    )

    net_revenue = total_revenue - refund_total

    # Transport & Hotel breakdowns
    train_bookings_count = all_bookings.filter(transport_type='TRAIN').count()
    flight_bookings_count = all_bookings.filter(transport_type='FLIGHT').count()
    bus_bookings_count = all_bookings.filter(transport_type='BUS').count()
    hotel_bookings_count = all_hotel_bookings.count()

    train_revenue = all_bookings.filter(transport_type='TRAIN', booking_status='CONFIRMED').aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')
    flight_revenue = all_bookings.filter(transport_type='FLIGHT', booking_status='CONFIRMED').aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')
    bus_revenue = all_bookings.filter(transport_type='BUS', booking_status='CONFIRMED').aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')

    # Inventory metrics
    total_trains = Train.objects.count()
    total_train_schedules = TrainSchedule.objects.count()
    total_flights = Flight.objects.count()
    total_flight_schedules = FlightSchedule.objects.count()
    total_buses = Bus.objects.count()
    total_bus_schedules = BusSchedule.objects.count()
    total_hotels = Hotel.objects.count()
    total_rooms = Room.objects.count()

    # Recent transactions
    recent_payments = Payment.objects.select_related('booking', 'booking__user').order_by('-created_at')[:8]
    recent_bookings = Booking.objects.select_related('user').order_by('-created_at')[:8]
    recent_hotel_bookings = HotelBooking.objects.select_related('hotel', 'user', 'room').order_by('-created_at')[:8]

    context = {
        'total_users': total_users,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_revenue': total_revenue,
        'net_revenue': net_revenue,
        'refund_total': refund_total,
        'train_bookings_count': train_bookings_count,
        'flight_bookings_count': flight_bookings_count,
        'bus_bookings_count': bus_bookings_count,
        'hotel_bookings_count': hotel_bookings_count,
        'train_revenue': train_revenue,
        'flight_revenue': flight_revenue,
        'bus_revenue': bus_revenue,
        'hotel_revenue': hotel_revenue,
        'total_trains': total_trains,
        'total_train_schedules': total_train_schedules,
        'total_flights': total_flights,
        'total_flight_schedules': total_flight_schedules,
        'total_buses': total_buses,
        'total_bus_schedules': total_bus_schedules,
        'total_hotels': total_hotels,
        'total_rooms': total_rooms,
        'recent_payments': recent_payments,
        'recent_bookings': recent_bookings,
        'recent_hotel_bookings': recent_hotel_bookings,
    }
    return render(request, 'admin_dashboard/home.html', context)


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def manage_trains(request):
    schedules = TrainSchedule.objects.select_related('train', 'source_station', 'destination_station').order_by('-journey_date')
    return render(request, 'admin_dashboard/trains.html', {'schedules': schedules})


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def manage_flights(request):
    schedules = FlightSchedule.objects.select_related('flight', 'flight__airline', 'origin_airport', 'destination_airport').order_by('-departure_datetime')
    return render(request, 'admin_dashboard/flights.html', {'schedules': schedules})


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def manage_buses(request):
    schedules = BusSchedule.objects.select_related('bus', 'bus__operator', 'route').order_by('-journey_date')
    return render(request, 'admin_dashboard/buses.html', {'schedules': schedules})


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def manage_hotels(request):
    hotels = Hotel.objects.prefetch_related('rooms', 'amenities').order_by('-is_featured', 'name')
    return render(request, 'admin_dashboard/hotels.html', {'hotels': hotels})


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def manage_bookings(request):
    query = request.GET.get('q')
    status_filter = request.GET.get('status')
    transport_filter = request.GET.get('transport')

    bookings = Booking.objects.select_related('user', 'payment').prefetch_related('passengers').order_by('-created_at')

    if query:
        bookings = bookings.filter(
            Q(pnr__icontains=query) | Q(user__username__icontains=query) | Q(user__email__icontains=query)
        )
    if status_filter:
        bookings = bookings.filter(booking_status=status_filter)
    if transport_filter:
        bookings = bookings.filter(transport_type=transport_filter)

    return render(request, 'admin_dashboard/bookings.html', {
        'bookings': bookings,
        'search_query': query,
        'selected_status': status_filter,
        'selected_transport': transport_filter,
    })


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def admin_cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        success, msg = booking.cancel_and_release_seats(reason="Admin cancellation & override")
        if success:
            messages.success(request, f"Admin cancelled booking {booking.pnr}: {msg}")
        else:
            messages.error(request, f"Could not cancel booking: {msg}")
    return redirect('admin_dashboard:manage_bookings')


@user_passes_test(is_staff_or_admin, login_url='accounts:login')
def manage_users(request):
    users = User.objects.annotate(
        booking_count=Count('bookings'),
        spent_total=Sum('bookings__total_amount', filter=Q(bookings__booking_status='CONFIRMED'))
    ).order_by('-date_joined')
    return render(request, 'admin_dashboard/users.html', {'users': users})
