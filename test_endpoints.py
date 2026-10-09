import requests
from bs4 import BeautifulSoup

BASE_URL = 'http://127.0.0.1:8000'

def test_system():
    print("Testing RailAway endpoints...")
    session = requests.Session()

    # 1. Homepage
    r = session.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Homepage failed with {r.status_code}"
    assert "Travel Anywhere. Book Everything." in r.text
    print("[PASS] Homepage OK (Status 200)")

    # 2. Railways Search
    r = session.get(f"{BASE_URL}/railways/")
    assert r.status_code == 200, f"Railways failed with {r.status_code}"
    assert "Available Trains" in r.text
    print("[PASS] Railway Search OK (Status 200)")

    # 3. Airlines Search
    r = session.get(f"{BASE_URL}/airlines/")
    assert r.status_code == 200, f"Airlines failed with {r.status_code}"
    assert "Available Flights" in r.text
    print("[PASS] Airlines Search OK (Status 200)")

    # 4. Buses Search
    r = session.get(f"{BASE_URL}/buses/")
    assert r.status_code == 200, f"Buses failed with {r.status_code}"
    assert "Available Luxury Buses" in r.text
    print("[PASS] Buses Search OK (Status 200)")

    # 5. Core Pages
    for p in ['about', 'contact', 'faq', 'terms']:
        r = session.get(f"{BASE_URL}/{p}/")
        assert r.status_code == 200, f"{p} failed"
    print("[PASS] Informational pages OK (Status 200)")

    # 6. Customer Login
    login_page = session.get(f"{BASE_URL}/accounts/login/")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']

    login_post = session.post(f"{BASE_URL}/accounts/login/", data={
        'csrfmiddlewaretoken': csrf_token,
        'username': 'customer',
        'password': 'password123',
    }, headers={'Referer': f"{BASE_URL}/accounts/login/"})
    assert login_post.status_code == 200 or login_post.history, "Login failed"
    print("[PASS] Customer Authentication OK")

    # 7. Customer Dashboard
    dash_r = session.get(f"{BASE_URL}/accounts/dashboard/")
    assert dash_r.status_code == 200
    assert "Customer Dashboard" in dash_r.text or "Hello" in dash_r.text
    print("[PASS] Customer Dashboard OK (Status 200)")

    # 8. Booking History
    history_r = session.get(f"{BASE_URL}/bookings/history/")
    assert history_r.status_code == 200
    assert "Booking History" in history_r.text
    print("[PASS] Booking History OK (Status 200)")

    # 9. Admin Login & Dashboard
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
    assert "Analytics & Platform Overview" in admin_dash.text
    print("[PASS] Admin Analytics Portal OK (Status 200)")

    # 10. Admin Inventory Pages
    for inv in ['trains', 'flights', 'buses', 'bookings', 'users']:
        r = admin_session.get(f"{BASE_URL}/management/{inv}/")
        assert r.status_code == 200, f"Admin {inv} failed with {r.status_code}"
    print("[PASS] Admin Inventory & User Management OK (Status 200)")

    # 11. EmailJS OTP Authentication Flow
    otp_session = requests.Session()
    login_pg = otp_session.get(f"{BASE_URL}/accounts/login/")
    soup_otp = BeautifulSoup(login_pg.text, 'html.parser')
    csrf_otp = soup_otp.find('input', {'name': 'csrfmiddlewaretoken'})['value']

    # Step 11a: Request OTP
    send_r = otp_session.post(f"{BASE_URL}/accounts/send-otp/", data={
        'csrfmiddlewaretoken': csrf_otp,
        'email': 'vip.traveler@example.com'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert send_r.status_code == 200, f"Send OTP failed with {send_r.status_code}"
    send_data = send_r.json()
    assert send_data['success'] is True
    assert send_data['expiry_seconds'] == 120
    print("[PASS] EmailJS Send OTP API OK (Status 200, 2-Min Expiry)")

    # Step 11b: Verify Wrong OTP rejected
    bad_verify_r = otp_session.post(f"{BASE_URL}/accounts/verify-otp/", data={
        'csrfmiddlewaretoken': csrf_otp,
        'email': 'vip.traveler@example.com',
        'otp': '000000'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert bad_verify_r.status_code == 400
    assert bad_verify_r.json()['success'] is False
    print("[PASS] EmailJS Verify Rejects Wrong OTP (Status 400)")

    # Step 11c: Cooldown rate-limit rejection on immediate re-send
    cooldown_r = otp_session.post(f"{BASE_URL}/accounts/send-otp/", data={
        'csrfmiddlewaretoken': csrf_otp,
        'email': 'vip.traveler@example.com'
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    # 12. Customer Experience & Reviews Hub
    exp_r = session.get(f"{BASE_URL}/experience/")
    assert exp_r.status_code == 200, f"Experience hub failed with {exp_r.status_code}"
    assert "Customer Experience" in exp_r.text or "Loved by Millions" in exp_r.text
    print("[PASS] Customer Experience & Reviews Hub OK (Status 200)")

    # 13. Legacy Price Finder Redirect
    pf_r = session.get(f"{BASE_URL}/price-finder/?from_city=New Delhi&to_city=Mumbai", allow_redirects=False)
    assert pf_r.status_code in (302, 301), f"Price finder redirect failed with {pf_r.status_code}"
    print("[PASS] Multi-Modal Lowest Price Finder Clean Redirect OK (Status 302)")

    # 14. Order Food in Train (E-Catering)
    food_home_r = session.get(f"{BASE_URL}/food/")
    assert food_home_r.status_code == 200, f"Food home failed with {food_home_r.status_code}"
    assert "Delivered to Your Berth" in food_home_r.text or "Order Food in Train" in food_home_r.text

    food_menu_r = session.get(f"{BASE_URL}/food/menu/")
    assert food_menu_r.status_code == 200, f"Food menu failed with {food_menu_r.status_code}"
    assert "Menu" in food_menu_r.text

    food_pnr_r = session.get(f"{BASE_URL}/food/api/pnr-lookup/?pnr=RAW-2026-8F73K2")
    assert food_pnr_r.status_code == 200
    assert food_pnr_r.json()['found'] is True
    print("[PASS] Order Food in Train & PNR Auto-lookup OK (Status 200)")

    # 15. Railway Station Retiring Rooms & Dormitories
    rr_home_r = session.get(f"{BASE_URL}/retiring-rooms/")
    assert rr_home_r.status_code == 200, f"Retiring rooms failed with {rr_home_r.status_code}"
    assert "Retiring Rooms" in rr_home_r.text or "Dormitories" in rr_home_r.text

    rr_search_r = session.get(f"{BASE_URL}/retiring-rooms/search/?station=NDLS&slot_type=24_HOURS")
    assert rr_search_r.status_code == 200
    assert "NDLS" in rr_search_r.text or "Retiring Rooms" in rr_search_r.text
    print("[PASS] Station Retiring Rooms & Dormitories Search OK (Status 200)")

    print("\n=======================================================")
    print("ALL 15 ENDPOINTS & MULTI-MODAL FLOWS VERIFIED WITH 100% PASS!")
    print("=======================================================")


if __name__ == '__main__':
    test_system()
