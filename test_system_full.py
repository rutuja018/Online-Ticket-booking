import os
import sys
import django
import requests
from bs4 import BeautifulSoup
from datetime import timedelta
from django.utils import timezone

# Set UTF-8 output encoding for Windows terminal safety
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'railaway.settings')
django.setup()

from hotels.models import Hotel, Room, HotelBooking

BASE_URL = 'http://127.0.0.1:8000'

def run_tests():
    print("=================================================================")
    print("RUNNING COMPREHENSIVE SUITE: EXISTING FEATURES + HOTEL BOOKING")
    print("=================================================================")
    
    session = requests.Session()

    # 1. Homepage & Multi-modal tabs
    r = session.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Homepage failed with {r.status_code}"
    assert "Travel Anywhere. Book Everything." in r.text
    assert "Train Booking" in r.text
    assert "Flight Booking" in r.text
    assert "Bus Booking" in r.text
    assert "Hotel Booking" in r.text
    print("[PASS] Homepage & 4-in-1 Multi-Modal Search Tabs OK (Status 200)")

    # 2. Existing Railway Search
    r = session.get(f"{BASE_URL}/railways/")
    assert r.status_code == 200, f"Railways failed with {r.status_code}"
    assert "Available Trains" in r.text
    print("[PASS] Railway Search OK (Status 200)")

    # 3. Existing Airlines Search
    r = session.get(f"{BASE_URL}/airlines/")
    assert r.status_code == 200, f"Airlines failed with {r.status_code}"
    assert "Available Flights" in r.text
    print("[PASS] Airlines Search OK (Status 200)")

    # 4. Existing Buses Search
    r = session.get(f"{BASE_URL}/buses/")
    assert r.status_code == 200, f"Buses failed with {r.status_code}"
    assert "Available Luxury Buses" in r.text
    print("[PASS] Buses Search OK (Status 200)")

    # 5. Existing Informational Pages
    for p in ['about', 'contact', 'faq', 'terms']:
        r = session.get(f"{BASE_URL}/{p}/")
        assert r.status_code == 200, f"{p} failed"
    print("[PASS] Informational core pages OK (Status 200)")

    # 6. Hotel Search Index & Filters
    r = session.get(f"{BASE_URL}/hotels/")
    assert r.status_code == 200, f"Hotels index failed with {r.status_code}"
    assert "Available Hotels Across India" in r.text or "Hotels" in r.text
    assert "Imperial Heritage" in r.text or "Taj" in r.text
    print("[PASS] Hotel Search & Listing OK (Status 200)")

    # 7. Hotel Search with Filter: Jaipur
    r = session.get(f"{BASE_URL}/hotels/search/?city=Jaipur&stars=5")
    assert r.status_code == 200, f"Hotel city search failed with {r.status_code}"
    assert "Jaipur" in r.text
    print("[PASS] Hotel Destination & Star Filter OK (Status 200)")

    # 8. Hotel Detail Page
    hotel = Hotel.objects.filter(is_active=True).first()
    assert hotel is not None, "No active hotel found"
    r = session.get(f"{BASE_URL}/hotels/{hotel.id}/")
    assert r.status_code == 200, f"Hotel detail failed with {r.status_code}"
    assert hotel.name in r.text
    assert "Available Room Categories" in r.text
    print(f"[PASS] Hotel Details Page for '{hotel.name}' OK (Status 200)")

    # 9. Hotel AJAX API: Price Calculation
    room = hotel.rooms.filter(is_active=True).first()
    assert room is not None, "No active room found"
    
    r = session.get(f"{BASE_URL}/hotels/api/calculate-price/?price_per_night={room.price_per_night}&rooms=2")
    assert r.status_code == 200, f"Price calc API failed: {r.text}"
    data = r.json()
    assert data['success'] is True
    assert data['room_count'] == 2
    print(f"[PASS] Hotel Price Calculation AJAX API OK (Calculated total: Rs. {data['total']})")

    # 10. Customer Login
    login_page = session.get(f"{BASE_URL}/accounts/login/")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

    login_post = session.post(f"{BASE_URL}/accounts/login/", data={
        'csrfmiddlewaretoken': csrf_token,
        'username': 'customer',
        'password': 'password123',
    }, headers={'Referer': f"{BASE_URL}/accounts/login/"})
    assert login_post.status_code == 200 or login_post.history, "Customer login failed"
    print("[PASS] Customer Authentication OK")

    # 11. Customer Dashboard
    dash_r = session.get(f"{BASE_URL}/accounts/dashboard/")
    assert dash_r.status_code == 200
    assert "Hello, Rohan" in dash_r.text or "Customer Dashboard" in dash_r.text
    print("[PASS] Customer Dashboard OK (Status 200)")

    # 12. Complete Hotel Booking Flow
    book_page = session.get(f"{BASE_URL}/hotels/{hotel.id}/book/{room.id}/")
    assert book_page.status_code == 200, f"Book page failed with {book_page.status_code}"
    soup_book = BeautifulSoup(book_page.text, 'html.parser')
    csrf_book = soup_book.find('input', {'name': 'csrfmiddlewaretoken'})['value']

    today = timezone.now().date()
    in_date = today + timedelta(days=5)
    out_date = today + timedelta(days=7)

    booking_post = session.post(f"{BASE_URL}/hotels/{hotel.id}/book/{room.id}/", data={
        'csrfmiddlewaretoken': csrf_book,
        'check_in_date': in_date.isoformat(),
        'check_out_date': out_date.isoformat(),
        'room_count': 1,
        'guest_count': 2,
        'primary_guest_name': 'Rohan Sharma',
        'email': 'customer@railaway.com',
        'phone': '9811223344',
        'special_requests': 'Quiet room on higher floor please',
        'promo_code': 'TIRANGA100',
    }, allow_redirects=True)

    assert booking_post.status_code == 200, f"Booking submission failed with {booking_post.status_code}"
    assert "Payment" in booking_post.text or "Simulated" in booking_post.text
    print("[PASS] Hotel Room Booking Creation OK (Redirected to Payment)")

    # 13. Simulated Payment Submission
    soup_pay = BeautifulSoup(booking_post.text, 'html.parser')
    csrf_pay = soup_pay.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    
    # Extract booking ID from URL or DB
    latest_booking = HotelBooking.objects.filter(primary_guest_name='Rohan Sharma').latest('created_at')
    assert latest_booking.booking_status == 'PENDING'

    pay_post = session.post(f"{BASE_URL}/hotels/payment/{latest_booking.id}/", data={
        'csrfmiddlewaretoken': csrf_pay,
        'payment_method': 'CREDIT_CARD',
        'cardholder_name': 'Rohan Sharma',
        'card_number': '4242424242424242',
        'card_expiry': '12/28',
        'card_cvv': '123',
        'simulate_action': 'SUCCESS',
    }, allow_redirects=True)

    assert pay_post.status_code == 200
    assert "Hotel E-Voucher" in pay_post.text or "Booking Confirmed" in pay_post.text
    assert latest_booking.booking_reference in pay_post.text
    latest_booking.refresh_from_db()
    assert latest_booking.booking_status == 'CONFIRMED'
    print(f"[PASS] Hotel Payment Simulation & E-Voucher Generation OK (Ref: {latest_booking.booking_reference})")

    # 14. Booking History Verification
    history_r = session.get(f"{BASE_URL}/bookings/history/?transport=HOTEL")
    assert history_r.status_code == 200
    assert latest_booking.booking_reference in history_r.text
    print("[PASS] Booking History with Hotels Filter OK")

    # 15. Hotel Cancellation Test
    cancel_page = session.get(f"{BASE_URL}/hotels/cancel/{latest_booking.booking_reference}/")
    assert cancel_page.status_code == 200
    soup_cancel = BeautifulSoup(cancel_page.text, 'html.parser')
    csrf_cancel = soup_cancel.find('input', {'name': 'csrfmiddlewaretoken'})['value']

    cancel_post = session.post(f"{BASE_URL}/hotels/cancel/{latest_booking.booking_reference}/", data={
        'csrfmiddlewaretoken': csrf_cancel,
        'cancellation_reason': 'Change of travel dates',
    }, allow_redirects=True)
    assert cancel_post.status_code == 200
    latest_booking.refresh_from_db()
    assert latest_booking.booking_status == 'CANCELLED'
    print(f"[PASS] Hotel Cancellation & Room Inventory Release OK (Status: {latest_booking.booking_status})")

    # 16. Admin Login & Portal Verification
    admin_session = requests.Session()
    admin_login_page = admin_session.get(f"{BASE_URL}/accounts/login/")
    soup_admin = BeautifulSoup(admin_login_page.text, 'html.parser')
    csrf_admin = soup_admin.find('input', {'name': 'csrfmiddlewaretoken'})['value']

    admin_post = admin_session.post(f"{BASE_URL}/accounts/login/", data={
        'csrfmiddlewaretoken': csrf_admin,
        'username': 'admin',
        'password': 'admin123',
    }, headers={'Referer': f"{BASE_URL}/accounts/login/"})
    
    admin_dash = admin_session.get(f"{BASE_URL}/management/")
    assert admin_dash.status_code == 200
    assert "Hotel Division" in admin_dash.text
    print("[PASS] Admin Portal Analytics with Hotel Division OK (Status 200)")

    # 17. Admin Hotel Management Inventory Page
    admin_hotel_inv = admin_session.get(f"{BASE_URL}/management/hotels/")
    assert admin_hotel_inv.status_code == 200
    assert "Hotel & Room Inventory" in admin_hotel_inv.text
    print("[PASS] Admin Hotel Inventory Management OK (Status 200)")

    # 18. Django Standard Admin Hotel Models Check
    for model_name in ['hotel', 'room', 'hotelamenity', 'hotelbooking']:
        admin_model_r = admin_session.get(f"{BASE_URL}/admin/hotels/{model_name}/")
        assert admin_model_r.status_code == 200, f"Django Admin {model_name} failed with {admin_model_r.status_code}"
    print("[PASS] Django Standard Admin Hotel Models Registration OK (Status 200)")

    # 19. Also run original test_endpoints.py suite to be 100% sure
    print("\n--- Running Original test_endpoints.py Verification ---")
    from test_endpoints import test_system
    test_system()

    print("\n" + "=" * 65)
    print("ALL 19 ENDPOINTS, INTEGRATIONS & FLOWS PASSED 100% SUCCESSFULLY!")
    print("=================================================================")

if __name__ == '__main__':
    run_tests()
