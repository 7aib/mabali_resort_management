# Mabali Resort Management

Full-featured Django-based resort management system with role-based access, real-time dashboards, inventory tracking, cash management, room reservations, and more.

## Features

### Authentication & Roles
- Custom User model (`AUTH_USER_MODEL`) with 10 roles: CEO, Accountant, HR Manager, Main Cashier, Cashier, Host, Sale, Customer, Driver, Waiter
- Role-based access control via `@roles_required` decorator on every view
- Login / logout with configurable `LOGIN_URL`
- User profile page
- Change password with strength meter and show/hide toggle
- Employee management — create, list, detail, edit, delete
- Phone number validation (`+92XXXXXXXXXX` format, 13 characters, project-wide)
- `SoftDeleteModelMixin` — employees are soft-deleted, never hard-deleted

### Dashboard
- Role-gated — only CEO, Accountant, HR Manager can access
- **POS by counter** — daily totals per counter type, exempting Water Sports (parasailing)
- **Guest entry stats** — total guests, adults, kids, walk-ins, members
- **Average spending per person** — Cash Counter Revenue / Total Guests
- **Revenue breakdown** — Cash Counter, Cash Register, Cash Handover
- **Active reservations** — table showing confirmed and checked-in reservations today
- **Room bookings** — today's check-ins, check-outs, and night-stay revenue
- **Trust amounts** — running trust balance
- **Free/complementary billing** — daily free billing entries
- **Expense and refund details** — ticket refunds, category-wise expenses
- **Pending inventory orders** — required and ordered item counts
- **All-time statistics** — lifetime totals for revenue, guests, transactions
- **Recent transactions** — latest 10 entries across all counters
- **Events** — upcoming events count
- Dark mode toggle (persisted via localStorage, dynamic stylesheet swap)

### Cash Counters
- **New Guest Entry** — form with AJAX phone lookup, auto-fills returning customer data
- **Daily Sales** — filterable by date and counter type
- **Customer Status Check** — lookup returning/old customers by phone
- **Cash Handover** — Cashier role only, end-of-shift handover with remarks
- **Cash Register** — Main Cashier role only, daily register reconciliation
- **Ticket Refund** — refund tracking with auto-calculated totals and reason selection (Weather Cancellation, Restaurant 6% Tax Paid Online, Other)
- Visit types: Paid, Complementary, Night Stay, Group, Decor Team Events
- Gate tracking: Main Gate, Event Gate, Lake Side Gate
- City tracking for guest origin (Islamabad, Rawalpindi, Lahore, Karachi, Peshawar, Quetta, Multan, Faisalabad, Other)
- Counter types: Main Restaurant LSR, Adventure Area, Reception, Water Sports, Water Sport Tuck Shop, Event Bar, Shooting Range, Tuck Shop (Main), Night Stay, Group/Event, Auction

### Inventory
- **Inventory Items** — full CRUD with name, category, supplier, stock quantity, unit, notes
- **Search and filter** — search by name/supplier/notes, filter by asset category
- **Stock Management** — aggregate stock view across all 11 categories (Jetski, Boat, Speedboat, Parasailing Boat, Vehicle, Equipment, Fuel, Ammo, Generator, Ambulance, Other)
- **Purchase Orders** — two-section view: Required items and Ordered items with badge counts
- **Fuel Entry** — vehicle assignment (J1-J11, B1-B5, SP1-SP3, P1-P2, etc.), status transitions, stock deduction on issue
- **Ammo Entry** — shooting range bullets, payment types (Paid via Cash, Paid via Tickets, Paid via Groups, Free Bullets), free bullet reason tracking
- **Generator Log** — run hours, fuel used in liters, notes
- **Ambulance Log** — patient name, patient type (Employee/Guest/Local), hospital selection (Khanpur, Haripur, Taxila, POF, Rawalpindi/Islamabad, Abbottabad, Others), start/end KM readings, driver
- **Status state machine** — centralized in `inventory/utils.py`:
  - `required → ordered → purchased` (standard procurement)
  - `required → issued` (direct issue from stock)
  - `required/ordered → cancelled`
  - `issued`, `purchased`, `cancelled` are terminal states
- **Stock validation** — cannot issue more than available `stock_quantity`; enforced at model `save()` level
- **Creation status enforcement** — only "Required" or "Issued" allowed as initial status
- Role-based visibility — Items and Add Item tabs only visible to CEO, Accountant, HR Manager, Main Cashier
- `InventoryItem` is a reference table — quantities tracked and updated in transaction log `save()` methods

### Reservations
- **Room management** — seeded rooms: huts, suites, rooms, honeymoon rooms (21 total)
- **Reservation create** — form with AJAX phone lookup, auto-creates or reuses Customer user
- **Reservation edit** — update guest info, dates, room, status, payment details
- **Reservation list** — all non-deleted reservations with search
- **Room status view** — live status for every room: available, occupied (today falls within stay), reserved (future check-in)
- **Overlap validation** — same room cannot be booked for overlapping dates (enforced in model `clean()` AND view-level check as safety net)
- **Status transitions** — Confirmed → Checked In → Checked Out / Cancelled
- **Payment tracking** — advance amount, amount received, balance due, discount, payment method (Cash/Credit/IBFT), payment type (Advance/Final), bank (Mabali FBIL)
- **Customer lookup API** — AJAX endpoint (`/reservations/api/customer-lookup/`) for real-time phone search
- **Checkout-day availability** — rooms become available on checkout day (`check_in <= today < check_out`)

### Finance
- **POS Entry** — Point of Sale entry with all 11 counter types and 3 payment methods (Cash, IBFT, Credit Card)
- Role-restricted to CEO, Accountant, HR Manager, Main Cashier

### Complementary / Free Billing
- **Free billing form** — bill type (QB Bill, Partial Bill, Without QT, Zoho Bill Full), department (8 departments), head (11 categories), status (Paid, Paid with Discount, Pending, Free, Package Bill)
- **File upload** for bill documents (`MEDIA_ROOT/bills/`)
- **Today's entries table** — all free billing entries for the current day
- Accessible to all logged-in users

### Error Logging
- **DatabaseLogHandler** — custom Django logging handler that writes to `ErrorLog` model
- **ErrorLogMiddleware** — captures request path, method, user, and IP for every exception
- **`@log_errors` decorator** — applied to every view across all apps; logs exceptions to DB then re-raises for Django's 500 handling
- **Read-only admin interface** — view all logged errors in Django admin
- Thread-safe via `threading.local()` for request context

### Project Configuration
- Project name, logo, icon, website URL, and hero image configurable via `mabali_resort_management/constants.py`
- Available in all templates via context processor
- Footer, navbar, sidebar, and login page all use config variables
- Paid visit price configurable (`PAID_VISIT_PRICE = 1500.00`)

### UI / Templates
- Gradient header + card-based design pattern across all pages
- Sticky footer pinned to bottom of page
- Dark mode toggle in navbar — persists via `localStorage` with dynamic stylesheet swap (`theme-default.css` ↔ `theme-dark.css`)
- Sidenav with role-based visibility:
  - Cash Handover → Cashier only
  - Cash Register → Main Cashier only
  - Finance, Rooms, Free/Complementary, Inventory → role-gated sections
- Generic reusable `PhoneLookup` JS module (`static/js/phone-lookup.js`) — configurable debounce, min length, callbacks
- Double-submit prevention on all forms
- Success/error message feedback via Django messages framework

## Tech Stack

- **Backend:** Django 5.2, Python 3.11+
- **Frontend:** Bootstrap 5, ApexCharts, Select2
- **Database:** SQLite (dev), PostgreSQL-ready
- **Dependencies:** Pillow (image uploads), python-dotenv

## Quick Start

```sh
# 1. Clone and set up virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set DJANGO_SECRET_KEY for production

# 4. Run migrations and start
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data   # optional: seed test rooms and data
python manage.py runserver
```

Open http://127.0.0.1:8000/

## URL Routes

| Path | App | View |
|---|---|---|
| `/` | authentication | Login |
| `/logout/` | authentication | Logout |
| `/profile/` | authentication | Profile |
| `/change-password/` | authentication | Change Password |
| `/employee_dashboard/` | authentication | Employee List |
| `/employee_create/` | authentication | Employee Create |
| `/employee/<pk>/` | authentication | Employee Detail |
| `/employee/<pk>/edit/` | authentication | Employee Edit |
| `/employee/<pk>/delete/` | authentication | Employee Delete |
| `/dashboard` | dashboard | Admin Dashboard |
| `/cash-counters/new-guest-entry/` | cash_counters | Guest Entry Form |
| `/cash-counters/daily-sales/` | cash_counters | Daily Sales |
| `/cash-counters/check-customer/` | cash_counters | Customer Status |
| `/cash-counters/cash-handover/` | cash_counters | Cash Handover |
| `/cash-counters/cash-register/` | cash_counters | Cash Register |
| `/cash-counters/ticket-refund/` | cash_counters | Ticket Refund |
| `/finance/pos-entry/` | finance | POS Entry |
| `/inventory/` | inventory | Inventory Dashboard |
| `/inventory/items/` | inventory | Item List |
| `/inventory/items/create/` | inventory | Item Create |
| `/inventory/items/<pk>/edit/` | inventory | Item Edit |
| `/inventory/items/<pk>/delete/` | inventory | Item Delete |
| `/inventory/generator-log/` | inventory | Generator Log |
| `/inventory/ambulance-log/` | inventory | Ambulance Log |
| `/inventory/fuel-entry/` | inventory | Fuel Entry |
| `/inventory/ammo-entry/` | inventory | Ammo Entry |
| `/inventory/purchase-orders/` | inventory | Purchase Orders |
| `/inventory/stock-management/` | inventory | Stock Management |
| `/reservations/` | reservations | Reservation List |
| `/reservations/create/` | reservations | Reservation Create |
| `/reservations/<pk>/edit/` | reservations | Reservation Edit |
| `/reservations/room-status/` | reservations | Room Status |
| `/reservations/api/customer-lookup/` | reservations | Customer Lookup API |
| `/complementary/free-billing/` | complementary | Free Billing |

## Project Structure

```
mabali_resort_management/
├── mabali_resort_management/   # Project settings, URLs, constants, mixins
├── authentication/             # User model, auth views, employee CRUD
├── dashboard/                  # Dashboard view, seed data command
├── inventory/                  # Items, fuel, ammo, generator, ambulance logs
├── cash_counters/              # Guest entry, sales, cash handover/register, refunds
├── finance/                    # POS entry
├── reservations/               # Rooms, reservations, room status
├── complementary/              # Free/complementary billing
├── error_logs/                 # Error logging handler, middleware, decorators
├── templates/                  # Base template, components (navbar, sidenav, footer)
├── static/                     # JS, CSS, vendor assets, themes
└── requirements.txt
```

## Running Tests

```sh
python manage.py test
```

Tests cover all 7 apps — 481+ tests total:
- `authentication/tests.py` — 84 tests (model, phone validation, forms, login/logout, profile, change password, employee CRUD, roles_required, edge cases)
- `cash_counters/tests.py` — 82 tests (5 models, 6 view endpoints, permission matrix, integration tests)
- `complementary/tests.py` — 42 tests (FreeBilling model, free_billing_view, all choices, permissions)
- `finance/tests.py` — 38 tests (POS model, pos_entry_view, role-based access, all counters/payment methods)
- `inventory/tests.py` — 127 tests (utils state machine, 5 models, status transitions, 11 views, role permissions, purchase orders, stock management)
- `dashboard/tests.py` — 50 tests (permissions, context keys, POS/guest/revenue/room/trust/inventory/events computations)
- `reservations/tests.py` — 58 tests (Room/Reservation models, create/edit/list/room_status/customer_lookup views, overlap validation, permissions)

## Configuration

- **Project name/logo:** Edit `mabali_resort_management/constants.py`
- **Time zone:** `Asia/Karachi` (set in `settings.py`)
- **Login URL:** `/` (set in `settings.py`)
- **Media files:** `MEDIA_ROOT = BASE_DIR / "media"` — bill uploads stored under `media/bills/`

## Notes

- **Role-based access** enforced via `@roles_required` decorator and `UserRoles` enum in `authentication/choices.py`
- **Inventory status transitions** enforced at model level via `inventory/utils.py` — `STATUS_TRANSITIONS` dict and `validate_status_transition()`
- **Stock validation** — `FuelTransactionLog.save()` and `AmmoTransactionLog.save()` check available `stock_quantity` before issuing
- **Room overlap validation** — `Reservation.clean()` uses `check_in_date__lte` / `check_out_date__gte` to catch same-day bookings; views also check directly as a safety net
- **All views log exceptions** to the database via `@log_errors` decorator
- **Dark mode** toggled from navbar, persisted via `localStorage`, applied via `html.dark-style` CSS class
- **Phone numbers** follow `+92XXXXXXXXXX` format (13 characters) project-wide
- **Timezone** set to `Asia/Karachi` — all `DateField` defaults use `timezone.localdate()` to avoid UTC/local mismatch
- **LOGIN_URL** set to `/` in `settings.py` (not Django's default `/accounts/login/`)
- **POS exempts Water Sports** from dashboard totals (parasailing is part of Water Sports)
- **Test suite** — 481+ tests across 7 apps: authentication (84), cash_counters (82), complementary (42), finance (38), inventory (127), dashboard (50), reservations (58)
