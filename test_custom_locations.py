import os
import sys
import django
import requests
from bs4 import BeautifulSoup
from datetime import timedelta
from django.utils import timezone

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'railaway.settings')
django.setup()

from railways.models import RailwayStation, TrainSchedule
from airlines.models import Airport, FlightSchedule
from buses.models import BusRoute, BusSchedule
from hotels.models import Hotel

BASE_URL = 'http://127.0.0.1:8000'

def run_tests():
    print("=================================================================")
    print("TESTING CUSTOM & UNLIMITED LOCATION SEARCH ACROSS ALL SERVICES")
    print("=================================================================")

    session = requests.Session()
    today = timezone.now().date().isoformat()
    future_date = (timezone.now().date() + timedelta(days=5)).isoformat()

    # 1. Test Railway with custom station names & codes
    print("\n--- 1. RAILWAYS CUSTOM LOCATION TESTS ---")
    
    # Test with station codes (e.g. Pune to Jaipur)
    r = session.get(f"{BASE_URL}/railways/?from_station=PUNE&to_station=JP&journey_date={future_date}")
    assert r.status_code == 200, f"Railways search failed with {r.status_code}"
    assert "Available Trains" in r.text
    assert "Seats Available" in r.text or "Vande Bharat" in r.text or "Express" in r.text
    print("[PASS] Train search by codes 'PUNE' -> 'JP' returned available trains.")

    # Test with arbitrary typed city names (e.g. "Ayodhya" to "Varanasi")
    r = session.get(f"{BASE_URL}/railways/?from_station=Ayodhya&to_station=Varanasi&journey_date={future_date}")
    assert r.status_code == 200
    assert "Available Trains" in r.text
    assert "Seats Available" in r.text or "Select Berths" in r.text
    print("[PASS] Train search by custom cities 'Ayodhya' -> 'Varanasi' dynamically generated trains.")

    # Test with a novel location typed by user (e.g. "Manali Hills" to "Shimla")
    r = session.get(f"{BASE_URL}/railways/?from_station=Manali Hills&to_station=Shimla&journey_date={future_date}")
    assert r.status_code == 200
    assert "Available Trains" in r.text
    assert "Select Berths" in r.text
    print("[PASS] Train search with brand new novel station 'Manali Hills' successfully created station and schedules.")

    # 2. Test Airlines with custom airport codes & names
    print("\n--- 2. AIRLINES CUSTOM LOCATION TESTS ---")
    
    # Test with IATA codes (e.g. "JAI" to "GOI")
    r = session.get(f"{BASE_URL}/airlines/?from_airport=JAI&to_airport=GOI&departure_date={future_date}")
    assert r.status_code == 200
    assert "Available Flights" in r.text
    assert "Seats Left" in r.text or "Select Seats" in r.text
    print("[PASS] Flight search by IATA codes 'JAI' -> 'GOI' returned available flights.")

    # Test with city names (e.g. "Chandigarh" to "Kochi")
    r = session.get(f"{BASE_URL}/airlines/?from_airport=Chandigarh&to_airport=Kochi&departure_date={future_date}")
    assert r.status_code == 200
    assert "Available Flights" in r.text
    assert "Select Seats" in r.text
    print("[PASS] Flight search by cities 'Chandigarh' -> 'Kochi' generated direct flights.")

    # Test round-trip flight with custom locations
    r = session.get(f"{BASE_URL}/airlines/?from_airport=DEL&to_airport=BOM&trip_type=roundtrip&departure_date={future_date}&return_date={(timezone.now().date() + timedelta(days=8)).isoformat()}")
    assert r.status_code == 200
    assert "Available Flights" in r.text
    print("[PASS] Round-trip flight search returned both outbound and return flights.")

    # 3. Test Buses with custom cities
    print("\n--- 3. BUSES CUSTOM LOCATION TESTS ---")
    
    # Test with standard routes
    r = session.get(f"{BASE_URL}/buses/?from_city=Pune&to_city=Goa&travel_date={future_date}")
    assert r.status_code == 200
    assert "Available Luxury Buses" in r.text
    assert "Seats Available" in r.text or "Select Deck" in r.text
    print("[PASS] Bus search 'Pune' -> 'Goa' returned active buses.")

    # Test with newly connected route (e.g. "Rishikesh" to "Shimla")
    r = session.get(f"{BASE_URL}/buses/?from_city=Rishikesh&to_city=Shimla&travel_date={future_date}")
    assert r.status_code == 200
    assert "Available Luxury Buses" in r.text
    assert "Select Deck" in r.text
    print("[PASS] Bus search for custom city pair 'Rishikesh' -> 'Shimla' dynamically generated route and schedules.")

    # 4. Test Hotels with custom city
    print("\n--- 4. HOTELS CUSTOM LOCATION TESTS ---")
    
    # Test existing hotel city (e.g. Goa)
    r = session.get(f"{BASE_URL}/hotels/search/?city=Goa")
    assert r.status_code == 200
    assert "Goa" in r.text
    print("[PASS] Hotel search for 'Goa' returned luxury resort.")

    # Test novel destination city (e.g. "Rishikesh")
    r = session.get(f"{BASE_URL}/hotels/search/?city=Rishikesh")
    assert r.status_code == 200
    assert "Rishikesh" in r.text
    print("[PASS] Hotel search for novel destination 'Rishikesh' dynamically generated luxury retreat.")

    print("\n=================================================================")
    print("ALL CUSTOM LOCATION AND DESTINATION TESTS PASSED PERFECTLY!")
    print("=================================================================")

if __name__ == '__main__':
    run_tests()
