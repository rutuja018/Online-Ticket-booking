from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Count, Min, Q
from django.utils import timezone

from .forms import ContactInquiryForm

from railways.models import RailwayStation, TrainSchedule
from airlines.models import Airport, FlightSchedule
from buses.models import BusRoute, BusSchedule
from hotels.models import Hotel
from experiences.models import CustomerReview

def home(request):
    """
    Homepage view providing:
    - Multi-modal unified search (Train, Flight, Bus, Hotel)
    - Featured journeys and popular destinations
    - Platform statistics and customer testimonials
    """
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    # Railway quick search data
    stations = RailwayStation.objects.filter(is_active=True).order_by('city')
    featured_trains = TrainSchedule.objects.filter(
        is_active=True, journey_date__gte=today
    ).select_related('train', 'source_station', 'destination_station')[:4]

    # Flight quick search data
    airports = Airport.objects.filter(is_active=True).order_by('city')
    featured_flights = FlightSchedule.objects.filter(
        is_active=True, departure_datetime__date__gte=today
    ).select_related('flight', 'flight__airline', 'origin_airport', 'destination_airport')[:4]

    # Bus quick search data
    bus_routes = BusRoute.objects.all()
    bus_source_cities = sorted(list(set(bus_routes.values_list('source_city', flat=True))))
    bus_dest_cities = sorted(list(set(bus_routes.values_list('destination_city', flat=True))))
    all_bus_cities = sorted(list(set(list(bus_source_cities) + list(bus_dest_cities))))
    featured_buses = BusSchedule.objects.filter(
        is_active=True, journey_date__gte=today
    ).select_related('bus', 'bus__operator', 'route')[:4]

    # Hotel quick search data
    hotel_cities = sorted(list(set(Hotel.objects.filter(is_active=True).values_list('city', flat=True))))
    featured_hotels = Hotel.objects.filter(is_active=True, is_featured=True).prefetch_related('rooms')[:4]
    if not featured_hotels.exists():
        featured_hotels = Hotel.objects.filter(is_active=True).prefetch_related('rooms')[:4]

    # Customer Experience Testimonials
    featured_reviews = CustomerReview.objects.filter(is_featured=True)[:6]
    if not featured_reviews.exists():
        featured_reviews = CustomerReview.objects.all()[:6]

    context = {
        'stations': stations,
        'airports': airports,
        'bus_source_cities': bus_source_cities,
        'bus_dest_cities': bus_dest_cities,
        'all_bus_cities': all_bus_cities,
        'hotel_cities': hotel_cities,
        'featured_trains': featured_trains,
        'featured_flights': featured_flights,
        'featured_buses': featured_buses,
        'featured_hotels': featured_hotels,
        'featured_reviews': featured_reviews,
        'today': today.isoformat(),
        'tomorrow': tomorrow.isoformat(),
    }
    return render(request, 'home.html', context)


def price_finder(request):
    """
    Redirects legacy price finder URL to home.
    """
    return redirect('core:home')


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    initial = {}
    if request.user.is_authenticated:
        full_name = request.user.get_full_name().strip()
        initial['name'] = full_name or request.user.username
        initial['email'] = request.user.email

    if request.method == 'POST':
        form = ContactInquiryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Thanks for reaching out. Our 24x7 travel desk will get back to you shortly.',
            )
            return redirect('core:contact')
        messages.error(request, 'Please correct the errors in the contact form below.')
    else:
        form = ContactInquiryForm(initial=initial)

    return render(request, 'core/contact.html', {'form': form})


def faq(request):
    return render(request, 'core/faq.html')


def terms(request):
    return render(request, 'core/terms.html')


def cancellation_policy(request):
    """
    Dedicated unified cancellation and refund policy hub for all 6 services:
    Trains, Flights, Buses, Hotels, Retiring Rooms, and Food in Train.
    """
    active_tab = request.GET.get('service', 'all').strip().lower()
    context = {
        'active_tab': active_tab,
    }
    return render(request, 'core/cancellation_policy.html', context)



def error_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)


def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)
