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
from .models import RailwayStation, Train, TrainSchedule, TrainSeat

def resolve_or_create_station(query_str):
    """
    Intelligently resolves a station query (ID, Station Code e.g. NDLS, City e.g. Pune,
    Full formatted string e.g. 'New Delhi Railway Station (NDLS)', or arbitrary custom location).
    If station is novel, creates a new RailwayStation record on the fly.
    """
    if not query_str or not str(query_str).strip():
        return None
    
    raw = str(query_str).strip()
    
    # 1. If numeric ID
    if raw.isdigit():
        stn = RailwayStation.objects.filter(id=int(raw)).first()
        if stn:
            return stn

    # 2. Extract code from parentheses like "New Delhi (NDLS)" or "Pune Junction (PUNE)"
    code_match = re.search(r'\(([A-Za-z0-9]+)\)', raw)
    if code_match:
        code_extracted = code_match.group(1).upper()
        stn = RailwayStation.objects.filter(code__iexact=code_extracted).first()
        if stn:
            return stn

    # 3. Direct Code match (e.g. "NDLS", "BOM", "PUNE", "JP")
    stn = RailwayStation.objects.filter(code__iexact=raw).first()
    if stn:
        return stn

    # 4. Direct City or Station name match
    stn = RailwayStation.objects.filter(Q(city__iexact=raw) | Q(name__iexact=raw)).first()
    if stn:
        return stn

    # 5. Substring / contains match
    stn = RailwayStation.objects.filter(Q(city__icontains=raw) | Q(name__icontains=raw)).first()
    if stn:
        return stn

    # 6. If not found, create a custom RailwayStation so user's choice is fully supported
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', raw).strip().title()
    if not clean_name:
        clean_name = "Custom Station"

    # Generate a unique 3-5 letter station code
    words = clean_name.split()
    if len(words) >= 3:
        suggested_code = (words[0][0] + words[1][0] + words[2][0]).upper()
    elif len(words) == 2:
        suggested_code = (words[0][:2] + words[1][:2]).upper()
    else:
        suggested_code = clean_name[:4].upper()

    base_code = suggested_code if len(suggested_code) >= 2 else "STN"
    final_code = base_code
    suffix = 1
    while RailwayStation.objects.filter(code=final_code).exists():
        final_code = f"{base_code[:3]}{suffix}"
        suffix += 1

    stn = RailwayStation.objects.create(
        code=final_code,
        name=f"{clean_name} Junction" if not clean_name.endswith(('Junction', 'Station', 'Cantt', 'Central', 'Terminus')) else clean_name,
        city=clean_name.replace(' Junction', '').replace(' Station', '').replace(' Cantt', '').strip(),
        state="India",
        is_active=True
    )
    return stn


def generate_on_demand_train_schedules(source_stn, dest_stn, journey_date):
    """
    Dynamically generates realistic train schedules between any two stations on a given date.
    Ensures that any custom or user-selected origin/destination pair always has bookable trains.
    """
    # Sample realistic train prototypes
    train_blueprints = [
        {'name': f"{source_stn.city} - {dest_stn.city} Vande Bharat Express", 'type': 'VANDE_BHARAT', 'coaches': 16, 'dep': time(6, 0), 'dur_factor': 0.75},
        {'name': f"{source_stn.city} - {dest_stn.city} Superfast Express", 'type': 'SUPERFAST', 'coaches': 20, 'dep': time(11, 30), 'dur_factor': 1.0},
        {'name': f"{source_stn.city} - {dest_stn.city} Rajdhani Express", 'type': 'RAJDHANI', 'coaches': 20, 'dep': time(16, 45), 'dur_factor': 0.85},
        {'name': f"{source_stn.city} - {dest_stn.city} Night Mail Express", 'type': 'EXPRESS', 'coaches': 22, 'dep': time(21, 15), 'dur_factor': 1.15},
    ]

    created_schedules = []
    # Seed random train numbers deterministically based on station ids
    seed_val = (source_stn.id * 1000 + dest_stn.id) % 90000 + 10000

    for idx, bp in enumerate(train_blueprints):
        train_num = str(seed_val + (idx * 2))
        train_obj, _ = Train.objects.get_or_create(
            train_number=train_num,
            defaults={
                'name': bp['name'],
                'train_type': bp['type'],
                'total_coaches': bp['coaches'],
                'is_active': True,
            }
        )

        # Realistic duration between 240 and 660 mins
        base_dur = 360
        dur_mins = int(base_dur * bp['dur_factor'])
        dep_time = bp['dep']
        dep_dt = datetime.combine(journey_date, dep_time)
        arr_dt = dep_dt + timedelta(minutes=dur_mins)
        arr_time = arr_dt.time()

        # Class fares
        base_sl = Decimal('480.00')
        fare_gen = Decimal('180.00')
        fare_sl = base_sl
        fare_3a = Decimal('1250.00')
        fare_2a = Decimal('1850.00')
        fare_1a = Decimal('2950.00')

        if bp['type'] == 'VANDE_BHARAT':
            fare_gen = Decimal('350.00')
            fare_sl = Decimal('720.00')
            fare_3a = Decimal('1580.00')
            fare_2a = Decimal('2250.00')
            fare_1a = Decimal('3450.00')
        elif bp['type'] == 'RAJDHANI':
            fare_gen = Decimal('380.00')
            fare_sl = Decimal('890.00')
            fare_3a = Decimal('1950.00')
            fare_2a = Decimal('2850.00')
            fare_1a = Decimal('4650.00')

        sched, created = TrainSchedule.objects.get_or_create(
            train=train_obj,
            source_station=source_stn,
            destination_station=dest_stn,
            journey_date=journey_date,
            defaults={
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'duration_minutes': dur_mins,
                'fare_general': fare_gen,
                'fare_sleeper': fare_sl,
                'fare_ac3': fare_3a,
                'fare_ac2': fare_2a,
                'fare_first_class': fare_1a,
                'runs_on': 'Daily (All 7 Days)',
                'is_active': True,
            }
        )

        if created or sched.seats.count() == 0:
            # Generate real seats for all classes
            coach_configs = [
                ('GEN1', 'GENERAL', ['CHAIR_CAR'], 20),
                ('S1', 'SLEEPER', ['LOWER', 'MIDDLE', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER'], 32),
                ('B1', 'AC_3_TIER', ['LOWER', 'MIDDLE', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER'], 32),
                ('A1', 'AC_2_TIER', ['LOWER', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER'], 24),
                ('H1', 'FIRST_CLASS', ['CABIN', 'COUPE'], 12),
            ]
            new_seats = []
            for coach, t_class, b_types, seat_count in coach_configs:
                for s_num in range(1, seat_count + 1):
                    b_type = b_types[(s_num - 1) % len(b_types)]
                    is_booked = (s_num in [3, 8, 14, 21])
                    new_seats.append(TrainSeat(
                        schedule=sched,
                        coach=coach,
                        seat_number=str(s_num),
                        berth_type=b_type,
                        travel_class=t_class,
                        is_booked=is_booked
                    ))
            TrainSeat.objects.bulk_create(new_seats, ignore_conflicts=True)

        created_schedules.append(sched)
    return created_schedules


def get_train_fare_strip(selected_source, selected_dest, selected_date, travel_class):
    """
    Computes lowest fares for a 7-day strip around selected_date.
    """
    strip = []
    today = timezone.now().date()
    start_d = max(today, selected_date - timedelta(days=3))
    dates = [start_d + timedelta(days=i) for i in range(7)]
    
    fares_list = []
    for d in dates:
        if selected_source and selected_dest and selected_source != selected_dest:
            existing_count = TrainSchedule.objects.filter(
                source_station=selected_source,
                destination_station=selected_dest,
                journey_date=d,
                is_active=True
            ).count()
            if existing_count == 0:
                generate_on_demand_train_schedules(selected_source, selected_dest, d)

        scheds = TrainSchedule.objects.filter(is_active=True, journey_date=d)
        if selected_source:
            scheds = scheds.filter(source_station=selected_source)
        if selected_dest:
            scheds = scheds.filter(destination_station=selected_dest)
        
        min_fare = None
        for s in scheds:
            f = s.get_fare_for_class(travel_class)
            if min_fare is None or f < min_fare:
                min_fare = f
        
        strip.append({
            'date_str': d.isoformat(),
            'day_name': d.strftime('%a'),
            'date_formatted': d.strftime('%d %b'),
            'day_num': d.day,
            'is_selected': (d == selected_date),
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


def train_fare_calendar_api(request):
    """
    Returns lowest available train fares for all days of a month.
    """
    source_query = request.GET.get('from_station')
    dest_query = request.GET.get('to_station')
    travel_class = request.GET.get('travel_class', 'SLEEPER')
    year_str = request.GET.get('year')
    month_str = request.GET.get('month')

    today = timezone.now().date()
    year = int(year_str) if year_str and year_str.isdigit() else today.year
    month = int(month_str) if month_str and month_str.isdigit() else today.month

    selected_source = resolve_or_create_station(source_query)
    selected_dest = resolve_or_create_station(dest_query)

    _, num_days = calendar.monthrange(year, month)
    days_data = []
    fares_list = []

    for d_num in range(1, num_days + 1):
        d_date = date(year, month, d_num)
        is_past = d_date < today

        if not is_past and selected_source and selected_dest and selected_source != selected_dest:
            existing_count = TrainSchedule.objects.filter(
                source_station=selected_source,
                destination_station=selected_dest,
                journey_date=d_date,
                is_active=True
            ).count()
            if existing_count == 0:
                generate_on_demand_train_schedules(selected_source, selected_dest, d_date)

        min_fare = None
        if not is_past:
            scheds = TrainSchedule.objects.filter(is_active=True, journey_date=d_date)
            if selected_source:
                scheds = scheds.filter(source_station=selected_source)
            if selected_dest:
                scheds = scheds.filter(destination_station=selected_dest)

            for s in scheds:
                f = s.get_fare_for_class(travel_class)
                if min_fare is None or f < min_fare:
                    min_fare = f

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


def search_trains(request):
    source_query = request.GET.get('from_station')
    dest_query = request.GET.get('to_station')
    journey_date_str = request.GET.get('journey_date')
    travel_class = request.GET.get('travel_class', 'SLEEPER')
    train_type = request.GET.get('train_type')

    stations = RailwayStation.objects.filter(is_active=True).order_by('city')
    
    selected_source = resolve_or_create_station(source_query)
    selected_dest = resolve_or_create_station(dest_query)
    selected_date = timezone.now().date()

    if journey_date_str:
        try:
            selected_date = datetime.strptime(journey_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()

    # Dynamic on-demand generation if valid origin and destination selected
    if selected_source and selected_dest and selected_source != selected_dest:
        existing_count = TrainSchedule.objects.filter(
            source_station=selected_source,
            destination_station=selected_dest,
            journey_date=selected_date,
            is_active=True
        ).count()

        if existing_count == 0:
            generate_on_demand_train_schedules(selected_source, selected_dest, selected_date)

    schedules = TrainSchedule.objects.filter(is_active=True).select_related(
        'train', 'source_station', 'destination_station'
    )

    if selected_source:
        schedules = schedules.filter(source_station=selected_source)

    if selected_dest:
        schedules = schedules.filter(destination_station=selected_dest)

    if journey_date_str or (selected_source and selected_dest):
        schedules = schedules.filter(journey_date=selected_date)
    else:
        # Default to today or future schedules
        today = timezone.now().date()
        schedules = schedules.filter(journey_date__gte=today)

    if train_type:
        schedules = schedules.filter(train__train_type=train_type)

    # Annotate with available seats and fares
    schedule_data = []
    for sched in schedules:
        available_seats = sched.available_seat_count(travel_class)
        fare = sched.get_fare_for_class(travel_class)
        schedule_data.append({
            'schedule': sched,
            'available_seats': available_seats,
            'fare': fare,
            'is_available': available_seats > 0,
        })

    sort_by = request.GET.get('sort', 'departure')
    if sort_by == 'price_asc':
        schedule_data.sort(key=lambda x: x['fare'])
    elif sort_by == 'duration':
        schedule_data.sort(key=lambda x: x['schedule'].duration_minutes)

    # Mark the cheapest schedule
    if schedule_data:
        min_f = min(item['fare'] for item in schedule_data)
        for item in schedule_data:
            item['is_lowest_price'] = (item['fare'] == min_f)

    # Calculate 7-day Fare Strip
    fare_strip = get_train_fare_strip(selected_source, selected_dest, selected_date, travel_class)

    # Updated station list including any newly created stations
    stations = RailwayStation.objects.filter(is_active=True).order_by('city')

    context = {
        'stations': stations,
        'results': schedule_data,
        'fare_strip': fare_strip,
        'selected_source': selected_source,
        'selected_dest': selected_dest,
        'raw_from': source_query or '',
        'raw_to': dest_query or '',
        'selected_date': selected_date.isoformat(),
        'selected_class': travel_class,
        'selected_train_type': train_type,
        'train_types': Train.TRAIN_TYPE_CHOICES,
        'sort_by': sort_by,
    }
    return render(request, 'railways/search.html', context)


def train_detail(request, schedule_id):
    schedule = get_object_or_404(
        TrainSchedule.objects.select_related('train', 'source_station', 'destination_station'),
        id=schedule_id, is_active=True
    )
    return render(request, 'railways/detail.html', {'schedule': schedule})


def train_seat_select(request, schedule_id):
    schedule = get_object_or_404(
        TrainSchedule.objects.select_related('train', 'source_station', 'destination_station'),
        id=schedule_id, is_active=True
    )
    travel_class = request.GET.get('class', 'SLEEPER')
    passengers_count = int(request.GET.get('passengers', 1))

    seats = TrainSeat.objects.filter(schedule=schedule, travel_class=travel_class).order_by('coach', 'id')
    
    # If no seats exist for this class, generate coach berths on demand
    if not seats.exists():
        coaches = {'GENERAL': 'GEN1', 'SLEEPER': 'S1', 'AC_3_TIER': 'B1', 'AC_2_TIER': 'A1', 'FIRST_CLASS': 'H1'}
        coach_name = coaches.get(travel_class, 'S1')
        berths = ['LOWER', 'MIDDLE', 'UPPER', 'LOWER', 'MIDDLE', 'UPPER', 'SIDE_LOWER', 'SIDE_UPPER']
        new_seats = []
        for i in range(1, 41):
            b_type = berths[(i - 1) % len(berths)]
            new_seats.append(TrainSeat(
                schedule=schedule,
                coach=coach_name,
                seat_number=str(i),
                berth_type=b_type,
                travel_class=travel_class,
                is_booked=(i in [3, 7, 14, 22]) # Demo occupied seats
            ))
        TrainSeat.objects.bulk_create(new_seats)
        seats = TrainSeat.objects.filter(schedule=schedule, travel_class=travel_class).order_by('coach', 'id')

    fare = schedule.get_fare_for_class(travel_class)

    context = {
        'schedule': schedule,
        'travel_class': travel_class,
        'passengers_count': passengers_count,
        'fare_per_seat': fare,
        'seats': seats,
    }
    return render(request, 'railways/seat_select.html', context)
