# RailAway — Multi-Modal Online Ticket Booking System

**RailAway** is a complete, production-style multi-modal online ticket booking web application built with **Python 3, Django, SQLite, Vanilla CSS3, and JavaScript**. It provides unified search, interactive seat maps, dynamic passenger forms, simulated payment processing, instant PNR generation, print-ready digital tickets, cancellation workflows, customer dashboard, and a custom analytics administration portal.

---

## Key Features

1. **Multi-Modal Unified Search**
   - **Trains:** Search by departure station, destination station, journey date, and class (General, Sleeper, 3A, 2A, 1A).
   - **Flights:** One-way and round-trip searches across airports with cabin classes (Economy, Premium Economy, Business, First).
   - **Buses:** Intercity searches with bus types (Volvo Multi-Axle, AC Sleeper 2+1, AC Seater 2+2, Semi-Sleeper).

2. **Interactive Seat Selection**
   - **Train Coach View:** Coach berth layout (Lower, Middle, Upper, Side Lower, Side Upper) with berth labels.
   - **Aircraft Fuselage View:** 3-3 and 2-2 cabin layout with aisle, window/aisle badges, and exit rows.
   - **Bus Multi-Deck View:** Lower & Upper Deck layouts with Sleeper single/double berths and Seater pushback seats.
   - **Atomic Concurrency Control:** Uses `select_for_update()` inside atomic database transactions to guarantee zero race-condition double-bookings.

3. **Simulated Payment Gateway**
   - Interactive payment methods: Credit/Debit Card (with live card formatting), UPI / QR Code Simulator, and Internet Banking.
   - Simulation Mode Switcher: Test both **Payment Success (Approved)** and **Bank Decline (Error)** scenarios.

4. **Printable E-Tickets & Boarding Passes**
   - Instant unique PNR generation (e.g. `RAW-2026-8F73K2`).
   - High-resolution boarding pass with simulated QR code, barcode, passenger table, and specialized `@media print` CSS.

5. **Customer Dashboard & Booking History**
   - KPI counters for total, upcoming, completed, and cancelled bookings.
   - Upcoming trip reminders and 1-click ticket access.
   - Searchable booking history with mode and status filters.

6. **Cancellation & Automated Refunds**
   - Server-side cancellation deadline validation (up to 4 hours before departure).
   - Dynamic tiered refund calculation (up to 90% refund).
   - Instant automatic release of reserved seats back to available inventory.

7. **Customer Experience & Verified Reviews Hub (`/experience/`)**
   - Platform satisfaction analytics (4.85 / 5 ★ average from 25,000+ travelers).
   - Mode-specific breakdown (Trains, Flights, Buses, Hotels, Food, Retiring Rooms).
   - Sentiment analytics (Punctuality, Cleanliness, Service, Value for Money).
   - Verified passenger review submission engine with star rating pickers and helpful upvoting.

8. **Multi-Modal Lowest Price Finder & Fare Comparison Engine (`/price-finder/`)**
   - Side-by-side fare matrix comparing minimum prices for Train vs Bus vs Flight vs Hotel on any route.
   - 100% "Lowest Price Guarantee" and "Cheapest Travel Mode" highlights.
   - Cost vs. Duration time-saving intelligence.
   - Integrated "Sort by: Lowest Price" filters on search pages.

9. **Order Food in Train — E-Catering Hot Meals Delivery (`/food/`)**
   - IRCTC-style train food delivery to passenger coach & berth upon arrival at the delivery station.
   - Delicious menus: Royal Indian Thalis, Hyderabadi Dum Biryani, Pure Jain Specials (No onion/garlic), Breakfast Combos & Beverages.
   - 1-Click PNR auto-lookup to auto-populate train, coach, and seat numbers.
   - Live real-time order tracking timeline (Placed -> Preparing -> Out for Delivery -> Delivered).

10. **Railway Station Retiring Rooms & AC Dormitories (`/retiring-rooms/`)**
    - Station transit lodging at major Indian railway stations (NDLS, CSMT, SBC, BSB, HWH, PUNE, JP).
    - Room categories: AC Dormitory Bed (from ₹250/12h), Non-AC Standard Room, AC Deluxe Double Room, Executive Suite.
    - Flexible hourly stay slots (12 Hours, 24 Hours, 48 Hours).
    - Printable Digital Station Stay Pass with QR entry code and concourse platform directions.

11. **Custom Admin Analytics Dashboard & Django Admin**
    - Analytics portal (`/management/`) with revenue metrics, transport distribution breakdown, inventory management, and refund overrides.
    - Fully configured Django standard admin (`/admin/`) with search, filters, and inlines.

---

## Technology Stack

- **Backend:** Python 3.13 + Django 5.2
- **Database:** SQLite (Relational ORM with indexed models and constraints)
- **Frontend:** HTML5, Modern Vanilla CSS3 (Custom Design System, CSS Variables, Glassmorphism, Print CSS), Vanilla JavaScript
- **Icons & Typography:** Font Awesome 6 + Google Fonts (*Outfit* and *Plus Jakarta Sans*)

---

## Project Structure

```text
railaway/
├── manage.py
├── requirements.txt
├── test_endpoints.py
├── railaway/                  # Project Configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                      # Global Views, Error Handlers, Context Processors & Seed Command
│   ├── context_processors.py
│   ├── views.py
│   ├── urls.py
│   └── management/commands/seed_demo_data.py
├── accounts/                  # User Registration, Authentication & Profile
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── railways/                  # Trains, Stations, Schedules & Berths
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── airlines/                  # Airlines, Airports, Flights & Cabins
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── buses/                     # Bus Operators, Buses, Routes & Decks
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── bookings/                  # Unified Bookings, Passengers & Cancellation Engine
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
├── payments/                  # Simulated Payment Gateway & Transactions
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── admin_dashboard/           # Custom Administrator Analytics Portal
│   ├── views.py
│   └── urls.py
├── templates/                 # Reusable HTML Templates
│   ├── base.html
│   ├── home.html
│   ├── components/            # Navbar, Footer, Alerts
│   ├── accounts/              # Login, Register, Profile, Dashboard
│   ├── railways/              # Search, Detail, Seat Select
│   ├── airlines/              # Search, Detail, Seat Select
│   ├── buses/                 # Search, Detail, Seat Select
│   ├── bookings/              # Review, Ticket, History, Cancel
│   ├── payments/              # Simulated Checkout
│   ├── admin_dashboard/       # Analytics, Inventory, Users
│   └── errors/                # 400, 403, 404, 500
├── static/
│   ├── css/                   # main.css, seat_map.css, ticket.css, dashboard.css
│   └── js/                    # main.js, search_tabs.js, seat_selection.js, payment.js
└── db.sqlite3
```

---

## Installation and Setup

### 1. Clone or Open Project Directory
```bash
cd "d:/ticket booking"
```

### 2. Create and Activate Virtual Environment (Optional)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Seed Demo Data
Populate realistic stations, trains, airports, flights, buses, schedules, demo bookings, and accounts:
```bash
python manage.py seed_demo_data
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Visit the application in your browser at: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## Demo Credentials

| Role | Username | Password | Email | Access |
|---|---|---|---|---|
| **Administrator** | `admin` | `admin123` | `admin@railaway.com` | `/management/` and `/admin/` |
| **Customer** | `customer` | `password123` | `customer@railaway.com` | Traveler Dashboard & Bookings |

---

## Running the Automated Test Suite

Run Django's built-in test runner:
```bash
python manage.py test
```

Run the end-to-end endpoint verification script:
```bash
python test_endpoints.py
```

---

## End-to-End User Flow

```text
Home Page (Unified Search Tabs)
  ↓
Search Trains / Flights / Buses
  ↓
View Available Schedules & Fares
  ↓
Interactive Seat Map (Pick Exact Berths / Cabin Seats / Sleeper Decks)
  ↓
Enter Passenger Info (Full Name, Age, ID Verification)
  ↓
Review Booking & Calculate Breakdown (Base Fare + Taxes + Fee - Discount)
  ↓
Demo Payment Gateway (Card / UPI / NetBanking Simulation)
  ↓
Payment Success → PNR Generated (e.g. RAW-2026-8F73K2)
  ↓
Confirmed E-Ticket & Boarding Pass (Printable with QR / Barcode)
  ↓
User Dashboard (View upcoming trips, booking history, or cancel with automated refund)
```
