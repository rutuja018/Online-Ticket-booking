import re
import random
import calendar
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import BusOperator, Bus, BusRoute, BusSchedule, BusSeat

def clean_bus_city(query_str):
    """Clean and normalize city string from user input or datalist."""
    if not query_str or not str(query_str).strip():
        return None
    raw = str(query_str).strip()
    # Remove any extra annotations in parentheses if present
    raw = re.sub(r'\(.*?\)', '', raw).strip()
    # Title-case clean city name
    clean = re.sub(r'[^a-zA-Z0-9\s]', '', raw).strip().title()
    return clean or None


def resolve_or_create_bus_route(source_city, dest_city):
    """Finds or dynamically creates a BusRoute between two cities."""
    if not source_city or not dest_city:
        return None
    
    # Try direct or case-insensitive match
    route = BusRoute.objects.filter(
        source_city__iexact=source_city,
        destination_city__iexact=dest_city
    ).first()

    if not route:
        # Substring search
        route = BusRoute.objects.filter(
            source_city__icontains=source_city,
            destination_city__icontains=dest_city
        ).first()

    if not route:
        # Create a new route on the fly
        bp = f"{source_city} Central Bus Stand, {source_city} Bypass Flyover, Railway Station Circle"
        dp = f"{dest_city} Main Bus Stand, {dest_city} City Center, Bypass Toll"
        dist = 320
        route = BusRoute.objects.create(
            source_city=source_city,
            destination_city=dest_city,
            boarding_points=bp,
            dropping_points=dp,
            distance_km=dist
        )
    return route


def generate_on_demand_bus_schedules(bus_route, travel_date):
    """
    Dynamically generates realistic luxury bus schedules for a given route and travel date.
    """
    operators = list(BusOperator.objects.all())
    if not operators:
        # Create standard operators
        z, _ = BusOperator.objects.get_or_create(name='Zingbus Smart Bus', defaults={'rating': Decimal('4.8'), 'contact_number': '+91 1800-102-8899'})
        ic, _ = BusOperator.objects.get_or_create(name='IntrCity SmartBus', defaults={'rating': Decimal('4.7'), 'contact_number': '+91 1800-120-7766'})
        srs, _ = BusOperator.objects.get_or_create(name='SRS Travels', defaults={'rating': Decimal('4.5'), 'contact_number': '+91 80-2680-9999'})
        vrl, _ = BusOperator.objects.get_or_create(name='VRL Travels', defaults={'rating': Decimal('4.6'), 'contact_number': '+91 1800-425-4555'})
        operators = [z, ic, srs, vrl]

    bus_slots = [
        {'hour': 6, 'min': 30, 'type': 'VOLVO', 'op_idx': 0, 'dur': 330, 'fare': Decimal('750.00'), 'sleeper': True},
        {'hour': 14, 'min': 0, 'type': 'SEMI_SLEEPER', 'op_idx': 1, 'dur': 360, 'fare': Decimal('580.00'), 'sleeper': False},
        {'hour': 18, 'min': 30, 'type': 'AC_SLEEPER', 'op_idx': 2, 'dur': 390, 'fare': Decimal('950.00'), 'sleeper': True},
        {'hour': 21, 'min': 45, 'type': 'VOLVO', 'op_idx': 3 if len(operators) > 3 else 0, 'dur': 340, 'fare': Decimal('1150.00'), 'sleeper': True},
        {'hour': 23, 'min': 15, 'type': 'AC_SLEEPER', 'op_idx': 0, 'dur': 360, 'fare': Decimal('890.00'), 'sleeper': True},
    ]

    created_schedules = []
    # Deterministic bus seed
    seed = (len(bus_route.source_city) * 100 + len(bus_route.destination_city)) % 900 + 100

    for idx, slot in enumerate(bus_slots):
        op = operators[slot['op_idx'] % len(operators)]
        bus_num = f"IND-{seed + idx * 10}-LX"

        bus_obj, _ = Bus.objects.get_or_create(
            bus_number=bus_num,
            defaults={
                'operator': op,
                'bus_type': slot['type'],
                'total_seats': 36 if slot['sleeper'] else 40,
                'is_ac': True,
                'has_sleeper': slot['sleeper'],
                'is_active': True,
            }
        )

        dep_time = time(slot['hour'], slot['min'])
        dep_dt = datetime.combine(travel_date, dep_time)
        arr_dt = dep_dt + timedelta(minutes=slot['dur'])
        arr_time = arr_dt.time()

        bs_obj, created = BusSchedule.objects.get_or_create(
            bus=bus_obj,
            route=bus_route,
            journey_date=travel_date,
            defaults={
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'duration_minutes': slot['dur'],
                'base_fare': slot['fare'],
                'amenities': 'Air Conditioning, Free High-Speed WiFi, USB Charging Ports, Water Bottle, Clean Blankets, GPS Live Tracking',
                'is_active': True,
            }
        )

        if created or bs_obj.seats.count() == 0:
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

        created_schedules.append(bs_obj)
    return created_schedules


def get_bus_fare_strip(from_city, to_city, travel_date, bus_type):
    """
    Computes lowest bus fares for a 7-day strip around travel_date.
    """
    strip = []
    today = timezone.now().date()
    start_d = max(today, travel_date - timedelta(days=3))
    dates = [start_d + timedelta(days=i) for i in range(7)]
    
    fares_list = []
    for d in dates:
        if from_city and to_city and from_city.lower() != to_city.lower():
            route = resolve_or_create_bus_route(from_city, to_city)
            if route:
                existing_count = BusSchedule.objects.filter(
                    route=route,
                    journey_date=d,
                    is_active=True
                ).count()
                if existing_count == 0:
                    generate_on_demand_bus_schedules(route, d)

        scheds = BusSchedule.objects.filter(is_active=True, journey_date=d)
        if from_city:
            scheds = scheds.filter(Q(route__source_city__iexact=from_city) | Q(route__source_city__icontains=from_city))
        if to_city:
            scheds = scheds.filter(Q(route__destination_city__iexact=to_city) | Q(route__destination_city__icontains=to_city))
        if bus_type:
            scheds = scheds.filter(bus__bus_type=bus_type)
        
        min_fare = None
        for s in scheds:
            if min_fare is None or s.base_fare < min_fare:
                min_fare = s.base_fare
        
        strip.append({
            'date_str': d.isoformat(),
            'day_name': d.strftime('%a'),
            'date_formatted': d.strftime('%d %b'),
            'day_num': d.day,
            'is_selected': (d == travel_date),
            'min_fare': float(min_fare) if min_fare is not None else None,
            'has_schedules': (min_fare is not None),
        })
        if min_fare is not None:
            fares_list.append(min_fare)

    if fares_list:
        lowest_f = min(fares_list)
        for item in strip:
            item['is_cheapest'] = (item['min_fare'] is not None and item['min_fare'] == lowest_f)
    else:
        for item in strip:
            item['is_cheapest'] = False

    return strip


def bus_fare_calendar_api(request):
    """
    Returns lowest available bus fares for all days of a month.
    """
    raw_from = request.GET.get('from_city')
    raw_to = request.GET.get('to_city')
    bus_type = request.GET.get('bus_type')
    year_str = request.GET.get('year')
    month_str = request.GET.get('month')

    from_city = clean_bus_city(raw_from)
    to_city = clean_bus_city(raw_to)

    today = timezone.now().date()
    year = int(year_str) if year_str and year_str.isdigit() else today.year
    month = int(month_str) if month_str and month_str.isdigit() else today.month

    _, num_days = calendar.monthrange(year, month)
    days_data = []
    fares_list = []

    route = None
    if from_city and to_city and from_city.lower() != to_city.lower():
        route = resolve_or_create_bus_route(from_city, to_city)

    for d_num in range(1, num_days + 1):
        d_date = date(year, month, d_num)
        is_past = d_date < today

        if not is_past and route:
            existing_count = BusSchedule.objects.filter(
                route=route,
                journey_date=d_date,
                is_active=True
            ).count()
            if existing_count == 0:
                generate_on_demand_bus_schedules(route, d_date)

        min_fare = None
        if not is_past:
            scheds = BusSchedule.objects.filter(is_active=True, journey_date=d_date)
            if from_city:
                scheds = scheds.filter(Q(route__source_city__iexact=from_city) | Q(route__source_city__icontains=from_city))
            if to_city:
                scheds = scheds.filter(Q(route__destination_city__iexact=to_city) | Q(route__destination_city__icontains=to_city))
            if bus_type:
                scheds = scheds.filter(bus__bus_type=bus_type)

            for s in scheds:
                if min_fare is None or s.base_fare < min_fare:
                    min_fare = s.base_fare

        days_data.append({
            'date_str': d_date.isoformat(),
            'day_num': d_num,
            'is_past': is_past,
            'min_fare': float(min_fare) if min_fare is not None else None,
            'has_schedules': (min_fare is not None),
        })
        if min_fare is not None:
            fares_list.append(min_fare)

    lowest_month_fare = min(fares_list) if fares_list else None
    for item in days_data:
        item['is_cheapest'] = (item['min_fare'] is not None and item['min_fare'] == lowest_month_fare)

    return JsonResponse({
        'success': True,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'days': days_data,
        'lowest_fare': float(lowest_month_fare) if lowest_month_fare is not None else None
    })


def search_buses(request):
    raw_from = request.GET.get('from_city')
    raw_to = request.GET.get('to_city')
    travel_date_str = request.GET.get('travel_date')
    bus_type = request.GET.get('bus_type')
    operator_id = request.GET.get('operator')

    from_city = clean_bus_city(raw_from)
    to_city = clean_bus_city(raw_to)

    today = timezone.now().date()
    travel_date = today
    if travel_date_str:
        try:
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
        except ValueError:
            travel_date = today

    # Dynamic route resolution and on-demand bus schedule generation
    if from_city and to_city and from_city.lower() != to_city.lower():
        route = resolve_or_create_bus_route(from_city, to_city)
        if route:
            existing_count = BusSchedule.objects.filter(
                route=route,
                journey_date=travel_date,
                is_active=True
            ).count()

            if existing_count == 0:
                generate_on_demand_bus_schedules(route, travel_date)

    routes = BusRoute.objects.all()
    source_cities = sorted(list(set(routes.values_list('source_city', flat=True))))
    dest_cities = sorted(list(set(routes.values_list('destination_city', flat=True))))
    operators = BusOperator.objects.all().order_by('name')

    schedules = BusSchedule.objects.filter(is_active=True).select_related(
        'bus', 'bus__operator', 'route'
    )

    if from_city:
        schedules = schedules.filter(
            Q(route__source_city__iexact=from_city) | Q(route__source_city__icontains=from_city)
        )

    if to_city:
        schedules = schedules.filter(
            Q(route__destination_city__iexact=to_city) | Q(route__destination_city__icontains=to_city)
        )

    if travel_date_str or (from_city and to_city):
        schedules = schedules.filter(journey_date=travel_date)
    else:
        schedules = schedules.filter(journey_date__gte=today)

    if bus_type:
        schedules = schedules.filter(bus__bus_type=bus_type)

    if operator_id:
        schedules = schedules.filter(bus__operator_id=operator_id)

    schedule_data = []
    for sched in schedules:
        available_seats = sched.available_seat_count()
        amenities_list = [a.strip() for a in sched.amenities.split(',') if a.strip()]
        schedule_data.append({
            'schedule': sched,
            'available_seats': available_seats,
            'fare': sched.base_fare,
            'amenities_list': amenities_list,
            'is_available': available_seats > 0,
        })

    # 7-day Fare Strip
    fare_strip = get_bus_fare_strip(from_city, to_city, travel_date, bus_type)

    # Updated routes list
    routes = BusRoute.objects.all()
    source_cities = sorted(list(set(routes.values_list('source_city', flat=True))))
    dest_cities = sorted(list(set(routes.values_list('destination_city', flat=True))))

    context = {
        'source_cities': source_cities,
        'dest_cities': dest_cities,
        'operators': operators,
        'bus_types': Bus.BUS_TYPE_CHOICES,
        'results': schedule_data,
        'fare_strip': fare_strip,
        'selected_from': from_city or raw_from or '',
        'selected_to': to_city or raw_to or '',
        'raw_from': raw_from or '',
        'raw_to': raw_to or '',
        'selected_date': travel_date.isoformat(),
        'selected_bus_type': bus_type,
        'selected_operator': operator_id,
    }
    return render(request, 'buses/search.html', context)


def bus_detail(request, schedule_id):
    schedule = get_object_or_404(
        BusSchedule.objects.select_related('bus', 'bus__operator', 'route'),
        id=schedule_id, is_active=True
    )
    boarding_points = [p.strip() for p in schedule.route.boarding_points.split(',') if p.strip()]
    dropping_points = [p.strip() for p in schedule.route.dropping_points.split(',') if p.strip()]
    amenities = [a.strip() for a in schedule.amenities.split(',') if a.strip()]

    context = {
        'schedule': schedule,
        'boarding_points': boarding_points,
        'dropping_points': dropping_points,
        'amenities': amenities,
    }
    return render(request, 'buses/detail.html', context)


def bus_seat_select(request, schedule_id):
    schedule = get_object_or_404(
        BusSchedule.objects.select_related('bus', 'bus__operator', 'route'),
        id=schedule_id, is_active=True
    )
    passengers_count = int(request.GET.get('passengers', 1))

    seats = BusSeat.objects.filter(schedule=schedule).order_by('deck', 'id')

    # If no seats exist for this schedule, generate standard lower and upper deck
    if not seats.exists():
        new_seats = []
        # Lower Deck (1 to 20)
        for i in range(1, 21):
            s_type = 'SLEEPER' if schedule.bus.has_sleeper and i > 12 else 'SEATER'
            new_seats.append(BusSeat(
                schedule=schedule,
                seat_number=f"L{i}",
                deck='LOWER',
                seat_type=s_type,
                is_ladies_only=(i in [1, 2]),
                is_booked=(i in [4, 7, 11])
            ))
        # Upper Deck (1 to 15)
        for i in range(1, 16):
            new_seats.append(BusSeat(
                schedule=schedule,
                seat_number=f"U{i}",
                deck='UPPER',
                seat_type='SLEEPER',
                is_ladies_only=False,
                is_booked=(i in [2, 8])
            ))
        BusSeat.objects.bulk_create(new_seats)
        seats = BusSeat.objects.filter(schedule=schedule).order_by('deck', 'id')

    lower_seats = seats.filter(deck='LOWER')
    upper_seats = seats.filter(deck='UPPER')

    context = {
        'schedule': schedule,
        'passengers_count': passengers_count,
        'fare_per_seat': schedule.base_fare,
        'lower_seats': lower_seats,
        'upper_seats': upper_seats,
    }
    return render(request, 'buses/seat_select.html', context)
