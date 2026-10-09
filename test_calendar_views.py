import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'railaway.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.urls import reverse
from bookings.models import Booking
from railways.models import TrainSchedule
from airlines.models import FlightSchedule
from buses.models import BusSchedule

def run_calendar_tests():
    print("=== Testing Calendar Features ===")
    
    # 1. Create or get test user
    user, created = User.objects.get_or_create(username='calendar_tester', defaults={'email': 'tester@example.com'})
    if created:
        user.set_password('testpass123')
        user.save()
    
    client = Client()
    client.force_login(user)

    # 2. Test Travel Itinerary Calendar Page
    cal_url = reverse('bookings:calendar')
    resp = client.get(cal_url)
    assert resp.status_code == 200, f"Expected 200 for calendar page, got {resp.status_code}"
    assert b"Travel Calendar" in resp.content or b"calendar" in resp.content
    print(" [PASS] /bookings/calendar/ renders successfully (200 OK)")

    # 3. Test Travel Calendar Events API
    api_url = reverse('bookings:calendar_events_api')
    resp = client.get(api_url, {'year': 2026, 'month': 10})
    assert resp.status_code == 200, f"Expected 200 for calendar events API, got {resp.status_code}"
    json_data = resp.json()
    assert json_data.get('success') is True, "Expected success: True"
    assert 'events' in json_data, "Expected events list in response"
    print(f" [PASS] /bookings/calendar/events/ returns JSON events successfully (Found {len(json_data['events'])} events)")

    # 4. Test ICS Export
    ics_url = reverse('bookings:export_calendar_ics')
    resp = client.get(ics_url)
    assert resp.status_code == 200, f"Expected 200 for ICS export, got {resp.status_code}"
    assert resp['Content-Type'].startswith('text/calendar'), f"Unexpected Content-Type: {resp['Content-Type']}"
    assert b"BEGIN:VCALENDAR" in resp.content
    assert b"END:VCALENDAR" in resp.content
    print(" [PASS] /bookings/calendar/export-ics/ generates standard RFC 5545 iCalendar stream")

    # 5. Test Railways Fare Calendar API
    rf_url = reverse('railways:fare_calendar_api')
    resp = client.get(rf_url, {'from_station': 'NDLS', 'to_station': 'BCT', 'travel_class': 'SLEEPER', 'year': 2026, 'month': 10})
    assert resp.status_code == 200, f"Expected 200 for railway fare calendar, got {resp.status_code}"
    r_json = resp.json()
    assert r_json.get('success') is True
    assert len(r_json.get('days', [])) == 31
    print(f" [PASS] /railways/api/fare-calendar/ returned 31-day price grid for Oct 2026")

    # 6. Test Airlines Fare Calendar API
    af_url = reverse('airlines:fare_calendar_api')
    resp = client.get(af_url, {'from_airport': 'DEL', 'to_airport': 'BOM', 'cabin_class': 'ECONOMY', 'year': 2026, 'month': 10})
    assert resp.status_code == 200, f"Expected 200 for flight fare calendar, got {resp.status_code}"
    a_json = resp.json()
    assert a_json.get('success') is True
    assert len(a_json.get('days', [])) == 31
    print(f" [PASS] /airlines/api/fare-calendar/ returned 31-day price grid for Oct 2026")

    # 7. Test Buses Fare Calendar API
    bf_url = reverse('buses:fare_calendar_api')
    resp = client.get(bf_url, {'from_city': 'Pune', 'to_city': 'Goa', 'year': 2026, 'month': 10})
    assert resp.status_code == 200, f"Expected 200 for bus fare calendar, got {resp.status_code}"
    b_json = resp.json()
    assert b_json.get('success') is True
    assert len(b_json.get('days', [])) == 31
    print(f" [PASS] /buses/api/fare-calendar/ returned 31-day price grid for Oct 2026")

    # 8. Test Search Results Pages with 7-Day Fare Strip
    r_search = client.get(reverse('railways:search'), {'from_station': 'NDLS', 'to_station': 'BCT', 'journey_date': '2026-10-15'})
    assert r_search.status_code == 200
    assert b"7-Day Lowest Fare Calendar" in r_search.content or b"fare-strip" in r_search.content
    print(" [PASS] Train search returns 7-day lowest fare strip HTML")

    a_search = client.get(reverse('airlines:search'), {'from_airport': 'DEL', 'to_airport': 'BOM', 'departure_date': '2026-10-15'})
    assert a_search.status_code == 200
    assert b"7-Day Lowest Flight Fares" in a_search.content or b"fare-strip" in a_search.content
    print(" [PASS] Flight search returns 7-day lowest flight fare strip HTML")

    b_search = client.get(reverse('buses:search'), {'from_city': 'Pune', 'to_city': 'Goa', 'travel_date': '2026-10-15'})
    assert b_search.status_code == 200
    assert b"7-Day Lowest Bus Fares" in b_search.content or b"fare-strip" in b_search.content
    print(" [PASS] Bus search returns 7-day lowest bus fare strip HTML")

    print("\n ALL CALENDAR TESTS PASSED SUCCESSFULLY! ")

if __name__ == '__main__':
    run_calendar_tests()
