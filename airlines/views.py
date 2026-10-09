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
from .models import Airport, Airline, Aircraft, Flight, FlightSchedule, FlightSeat

def resolve_or_create_airport(query_str):
    """
    Intelligently resolves an airport query (ID, 3-letter IATA Code e.g. DEL, City e.g. Goa,
    Full formatted string e.g. 'Kempegowda International Airport (BLR)', or custom location).
    If novel, creates a new Airport record on the fly.
    """
    if not query_str or not str(query_str).strip():
        return None

    raw = str(query_str).strip()

    # 1. Numeric ID
    if raw.isdigit():
        apt = Airport.objects.filter(id=int(raw)).first()
        if apt:
            return apt

    # 2. Extract 3-letter code from parentheses like "Indira Gandhi (DEL)"
    code_match = re.search(r'\(([A-Za-z0-9]+)\)', raw)
    if code_match:
        code_extracted = code_match.group(1).upper()
        apt = Airport.objects.filter(code__iexact=code_extracted).first()
        if apt:
            return apt

    # 3. Direct Code match (e.g. "DEL", "BOM", "GOI", "BLR")
    apt = Airport.objects.filter(code__iexact=raw).first()
    if apt:
        return apt

    # 4. Direct City or Name match
    apt = Airport.objects.filter(Q(city__iexact=raw) | Q(name__iexact=raw)).first()
    if apt:
        return apt

    # 5. Substring / contains match
    apt = Airport.objects.filter(Q(city__icontains=raw) | Q(name__icontains=raw)).first()
    if apt:
        return apt

    # 6. Novel airport creation
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', raw).strip().title()
    if not clean_name:
        clean_name = "Custom Airport"

    words = clean_name.split()
    if len(words) >= 3:
        suggested_code = (words[0][0] + words[1][0] + words[2][0]).upper()
    elif len(words) == 2:
        suggested_code = (words[0][:2] + words[1][0]).upper()
    else:
        suggested_code = clean_name[:3].upper()

    base_code = suggested_code if len(suggested_code) == 3 else "AIR"
    final_code = base_code
    suffix = 1
    while Airport.objects.filter(code=final_code).exists():
        final_code = f"{base_code[:2]}{suffix}"
        suffix += 1

    apt = Airport.objects.create(
        code=final_code,
        name=f"{clean_name} International Airport" if not 'Airport' in clean_name else clean_name,
        city=clean_name.replace(' International Airport', '').replace(' Airport', '').strip(),
        country="India",
        terminal="Terminal 1 / 2",
        is_active=True
    )
    return apt


def generate_on_demand_flight_schedules(origin_apt, dest_apt, departure_date):
    """
    Dynamically generates realistic flight schedules between any two airports on a given date.
    """
    airlines = list(Airline.objects.all())
    if not airlines:
        # Fallback airlines
        ai, _ = Airline.objects.get_or_create(code='AI', defaults={'name': 'Air India', 'logo_icon': 'fa-plane-departure'})
        indigo, _ = Airline.objects.get_or_create(code='6E', defaults={'name': 'IndiGo Airlines', 'logo_icon': 'fa-plane-tail'})
        vistara, _ = Airline.objects.get_or_create(code='UK', defaults={'name': 'Vistara', 'logo_icon': 'fa-paper-plane'})
        akasa, _ = Airline.objects.get_or_create(code='QP', defaults={'name': 'Akasa Air', 'logo_icon': 'fa-plane'})
        airlines = [ai, indigo, vistara, akasa]

    aircraft_obj = Aircraft.objects.first()
    if not aircraft_obj:
        aircraft_obj = Aircraft.objects.create(model_name='Airbus A320neo', total_capacity=186)

    flight_slots = [
        {'hour': 6, 'min': 45, 'airline_idx': 0, 'flight_sfx': '101', 'stops': 0, 'eco': Decimal('4200.00'), 'prem': Decimal('6500.00'), 'biz': Decimal('14500.00'), 'fst': Decimal('26000.00')},
        {'hour': 11, 'min': 15, 'airline_idx': 1, 'flight_sfx': '205', 'stops': 0, 'eco': Decimal('4600.00'), 'prem': Decimal('6900.00'), 'biz': Decimal('15200.00'), 'fst': Decimal('27500.00')},
        {'hour': 15, 'min': 30, 'airline_idx': 2, 'flight_sfx': '309', 'stops': 0, 'eco': Decimal('5100.00'), 'prem': Decimal('7600.00'), 'biz': Decimal('16800.00'), 'fst': Decimal('29000.00')},
        {'hour': 19, 'min': 50, 'airline_idx': 3 if len(airlines) > 3 else 0, 'flight_sfx': '415', 'stops': 0, 'eco': Decimal('3900.00'), 'prem': Decimal('5800.00'), 'biz': Decimal('13200.00'), 'fst': Decimal('23500.00')},
    ]

    created_schedules = []
    for slot in flight_slots:
        airline = airlines[slot['airline_idx'] % len(airlines)]
        fl_num = f"{airline.code}-{origin_apt.code[:2]}{dest_apt.code[:1]}{slot['flight_sfx']}"

        fl_obj, _ = Flight.objects.get_or_create(
            flight_number=fl_num,
            defaults={'airline': airline, 'aircraft': aircraft_obj, 'is_active': True}
        )

        dep_dt = datetime.combine(departure_date, time(slot['hour'], slot['min']))
        dep_dt = timezone.make_aware(dep_dt, timezone.get_current_timezone())
        duration_mins = 125
        arr_dt = dep_dt + timedelta(minutes=duration_mins)

        fl_sched, created = FlightSchedule.objects.get_or_create(
            flight=fl_obj,
            origin_airport=origin_apt,
            destination_airport=dest_apt,
            departure_datetime=dep_dt,
            defaults={
                'arrival_datetime': arr_dt,
                'duration_minutes': duration_mins,
                'stops': slot['stops'],
                'fare_economy': slot['eco'],
                'fare_premium_economy': slot['prem'],
                'fare_business': slot['biz'],
                'fare_first_class': slot['fst'],
                'baggage_allowance': '15 Kg Check-in + 7 Kg Cabin',
                'meal_included': True,
                'is_active': True,
            }
        )

        if created or fl_sched.seats.count() == 0:
            fl_seats = []
            # Economy (Rows 10-25)
            for r in range(10, 26):
                for c in ['A', 'B', 'C', 'D', 'E', 'F']:
                    st = 'WINDOW' if c in ['A', 'F'] else ('AISLE' if c in ['C', 'D'] else 'MIDDLE')
                    fl_seats.append(FlightSeat(
                        schedule=fl_sched,
                        seat_number=f"{r}{c}",
                        row_number=r,
                        column_letter=c,
                        cabin_class='ECONOMY',
                        seat_type=st,
                        is_booked=(r in [12, 17] and c in ['A', 'D'])
                    ))
            # Business (Rows 3-5)
            for r in range(3, 6):
                for c in ['A', 'C', 'D', 'F']:
                    st = 'WINDOW' if c in ['A', 'F'] else 'AISLE'
                    fl_seats.append(FlightSeat(
                        schedule=fl_sched,
                        seat_number=f"{r}{c}",
                        row_number=r,
                        column_letter=c,
                        cabin_class='BUSINESS',
                        seat_type=st,
                        is_booked=(r == 4 and c == 'A')
                    ))
            FlightSeat.objects.bulk_create(fl_seats, ignore_conflicts=True)

        created_schedules.append(fl_sched)
    return created_schedules


def get_flight_fare_strip(selected_origin, selected_dest, selected_date, cabin_class):
    """
    Computes lowest flight fares for a 7-day strip around selected_date.
    """
    strip = []
    today = timezone.now().date()
    start_d = max(today, selected_date - timedelta(days=3))
    dates = [start_d + timedelta(days=i) for i in range(7)]
    
    fares_list = []
    for d in dates:
        if selected_origin and selected_dest and selected_origin != selected_dest:
            existing_count = FlightSchedule.objects.filter(
                origin_airport=selected_origin,
                destination_airport=selected_dest,
                departure_datetime__date=d,
                is_active=True
            ).count()
            if existing_count == 0:
                generate_on_demand_flight_schedules(selected_origin, selected_dest, d)

        scheds = FlightSchedule.objects.filter(is_active=True, departure_datetime__date=d)
        if selected_origin:
            scheds = scheds.filter(origin_airport=selected_origin)
        if selected_dest:
            scheds = scheds.filter(destination_airport=selected_dest)
        
        min_fare = None
        for s in scheds:
            f = s.get_fare_for_class(cabin_class)
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


def flight_fare_calendar_api(request):
    """
    Returns lowest available flight fares for all days of a month.
    """
    origin_query = request.GET.get('from_airport')
    dest_query = request.GET.get('to_airport')
    cabin_class = request.GET.get('cabin_class', 'ECONOMY')
    year_str = request.GET.get('year')
    month_str = request.GET.get('month')

    today = timezone.now().date()
    year = int(year_str) if year_str and year_str.isdigit() else today.year
    month = int(month_str) if month_str and month_str.isdigit() else today.month

    selected_origin = resolve_or_create_airport(origin_query)
    selected_dest = resolve_or_create_airport(dest_query)

    _, num_days = calendar.monthrange(year, month)
    days_data = []
    fares_list = []

    for d_num in range(1, num_days + 1):
        d_date = date(year, month, d_num)
        is_past = d_date < today

        if not is_past and selected_origin and selected_dest and selected_origin != selected_dest:
            existing_count = FlightSchedule.objects.filter(
                origin_airport=selected_origin,
                destination_airport=selected_dest,
                departure_datetime__date=d_date,
                is_active=True
            ).count()
            if existing_count == 0:
                generate_on_demand_flight_schedules(selected_origin, selected_dest, d_date)

        min_fare = None
        if not is_past:
            scheds = FlightSchedule.objects.filter(is_active=True, departure_datetime__date=d_date)
            if selected_origin:
                scheds = scheds.filter(origin_airport=selected_origin)
            if selected_dest:
                scheds = scheds.filter(destination_airport=selected_dest)

            for s in scheds:
                f = s.get_fare_for_class(cabin_class)
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


def search_flights(request):
    origin_query = request.GET.get('from_airport')
    dest_query = request.GET.get('to_airport')
    dep_date_str = request.GET.get('departure_date')
    return_date_str = request.GET.get('return_date')
    trip_type = request.GET.get('trip_type', 'oneway')
    cabin_class = request.GET.get('cabin_class', 'ECONOMY')
    airline_id = request.GET.get('airline')
    max_stops = request.GET.get('stops')

    airports = Airport.objects.filter(is_active=True).order_by('city')
    airlines = Airline.objects.all().order_by('name')

    selected_origin = resolve_or_create_airport(origin_query)
    selected_dest = resolve_or_create_airport(dest_query)

    today = timezone.now().date()
    dep_date = today
    if dep_date_str:
        try:
            dep_date = datetime.strptime(dep_date_str, '%Y-%m-%d').date()
        except ValueError:
            dep_date = today

    # Dynamic on-demand flight schedule generation
    if selected_origin and selected_dest and selected_origin != selected_dest:
        existing_count = FlightSchedule.objects.filter(
            origin_airport=selected_origin,
            destination_airport=selected_dest,
            departure_datetime__date=dep_date,
            is_active=True
        ).count()

        if existing_count == 0:
            generate_on_demand_flight_schedules(selected_origin, selected_dest, dep_date)

        # Handle round-trip return flight generation if requested
        if trip_type == 'roundtrip' and return_date_str:
            try:
                ret_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
            except ValueError:
                ret_date = dep_date + timedelta(days=2)

            ret_existing_count = FlightSchedule.objects.filter(
                origin_airport=selected_dest,
                destination_airport=selected_origin,
                departure_datetime__date=ret_date,
                is_active=True
            ).count()

            if ret_existing_count == 0:
                generate_on_demand_flight_schedules(selected_dest, selected_origin, ret_date)

    schedules = FlightSchedule.objects.filter(is_active=True).select_related(
        'flight', 'flight__airline', 'flight__aircraft', 'origin_airport', 'destination_airport'
    )

    if selected_origin:
        schedules = schedules.filter(origin_airport=selected_origin)

    if selected_dest:
        schedules = schedules.filter(destination_airport=selected_dest)

    if dep_date_str or (selected_origin and selected_dest):
        schedules = schedules.filter(departure_datetime__date=dep_date)
    else:
        schedules = schedules.filter(departure_datetime__date__gte=today)

    if airline_id:
        schedules = schedules.filter(flight__airline_id=airline_id)

    if max_stops is not None and max_stops != '':
        schedules = schedules.filter(stops__lte=int(max_stops))

    # Calculate available seats and fares
    schedule_data = []
    for sched in schedules:
        available_seats = sched.available_seat_count(cabin_class)
        fare = sched.get_fare_for_class(cabin_class)
        schedule_data.append({
            'schedule': sched,
            'available_seats': available_seats,
            'fare': fare,
            'is_available': available_seats > 0,
        })

    # Return flight search if round trip
    return_schedules_data = []
    if trip_type == 'roundtrip' and selected_origin and selected_dest:
        return_schedules = FlightSchedule.objects.filter(
            is_active=True,
            origin_airport=selected_dest,
            destination_airport=selected_origin
        ).select_related('flight', 'flight__airline', 'flight__aircraft', 'origin_airport', 'destination_airport')

        if return_date_str:
            try:
                ret_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
                return_schedules = return_schedules.filter(departure_datetime__date=ret_date)
            except ValueError:
                pass

        for ret_sched in return_schedules:
            av_seats = ret_sched.available_seat_count(cabin_class)
            ret_fare = ret_sched.get_fare_for_class(cabin_class)
            return_schedules_data.append({
                'schedule': ret_sched,
                'available_seats': av_seats,
                'fare': ret_fare,
                'is_available': av_seats > 0,
            })

    # Compute 7-Day Fare Strip
    fare_strip = get_flight_fare_strip(selected_origin, selected_dest, dep_date, cabin_class)

    airports = Airport.objects.filter(is_active=True).order_by('city')

    context = {
        'airports': airports,
        'airlines': airlines,
        'results': schedule_data,
        'return_results': return_schedules_data,
        'fare_strip': fare_strip,
        'selected_origin': selected_origin,
        'selected_dest': selected_dest,
        'raw_from': origin_query or '',
        'raw_to': dest_query or '',
        'selected_dep_date': dep_date.isoformat(),
        'selected_return_date': return_date_str or (dep_date + timedelta(days=2)).isoformat(),
        'trip_type': trip_type,
        'selected_cabin': cabin_class,
        'selected_airline': airline_id,
        'selected_stops': max_stops,
        'cabin_choices': FlightSeat.CABIN_CHOICES,
    }
    return render(request, 'airlines/search.html', context)


def flight_detail(request, schedule_id):
    schedule = get_object_or_404(
        FlightSchedule.objects.select_related('flight', 'flight__airline', 'flight__aircraft', 'origin_airport', 'destination_airport'),
        id=schedule_id, is_active=True
    )
    return render(request, 'airlines/detail.html', {'schedule': schedule})


def flight_seat_select(request, schedule_id):
    schedule = get_object_or_404(
        FlightSchedule.objects.select_related('flight', 'flight__airline', 'flight__aircraft', 'origin_airport', 'destination_airport'),
        id=schedule_id, is_active=True
    )
    cabin_class = request.GET.get('class', 'ECONOMY').upper()
    valid_classes = [c[0] for c in FlightSeat.CABIN_CHOICES]
    if cabin_class not in valid_classes:
        cabin_class = 'ECONOMY'
    passengers_count = int(request.GET.get('passengers', 1))

    # Ensure seats exist for this schedule and class
    schedule.generate_seats_for_class(cabin_class)
    seats = FlightSeat.objects.filter(schedule=schedule, cabin_class=cabin_class).order_by('row_number', 'column_letter')

    fare = schedule.get_fare_for_class(cabin_class)

    context = {
        'schedule': schedule,
        'cabin_class': cabin_class,
        'passengers_count': passengers_count,
        'fare_per_seat': fare,
        'seats': seats,
    }
    return render(request, 'airlines/seat_select.html', context)
