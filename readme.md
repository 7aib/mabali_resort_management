# Mabali Resort Management

Lightweight Django-based resort management dashboard used for demos and internal tools.

## Overview

Mabali Resort Management is a Django project that provides a simple admin/dashboard interface, authentication, and inventory modules. The repo includes frontend assets (Bootstrap, ApexCharts) under `static/` and server-side templates under `templates/`.

## Quick links

- Project entry: [manage.py](manage.py)  
- Settings: [`mabali_resort_management.settings`](mabali_resort_management/settings.py) — see [`AUTH_USER_MODEL`](mabali_resort_management/settings.py)  
- Authentication app:
  - User model: [`authentication.models.User`](authentication/models.py)
  - Login/logout views: [`authentication.views.login_view`](authentication/views.py), [`authentication.views.logout_view`](authentication/views.py)
  - Login template: [authentication/templates/login.html](authentication/templates/login.html)
- Dashboard:
  - View: [`dashboard.views.dashboard_view`](dashboard/views.py)
  - Template: [dashboard/templates/dashboard/index.html](dashboard/templates/dashboard/index.html)
- Inventory:
  - Core model: [`inventory.models.InventoryItem`](inventory/models.py)
  - Views: [inventory/views.py](inventory/views.py)
- Base template: [templates/base.html](templates/base.html)
- Key frontend scripts:
  - Main: [static/js/main.js](static/js/main.js)
  - Charts: [static/js/dashboards-analytics.js](static/js/dashboards-analytics.js)
  - Toasts: [static/js/ui-toasts.js](static/js/ui-toasts.js)

## Repo structure (high level)

- authentication/ — custom user model, auth views, forms, templates, migrations  
- dashboard/ — analytics pages and dummy data used for the UI  
- inventory/ — inventory models and simple views  
- mabali_resort_management/ — Django project settings, wsgi/asgi, mixins  
- static/ — compiled frontend assets (JS, CSS, vendor)  
- templates/ — shared templates and components (navbar, sidenav, footer)

## Local development

1. Create & activate virtualenv:
   ```sh
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```
2. Install requirements (add your requirements as needed):
   ```sh
   pip install django
   ```
3. Set up DB and run server:
   ```sh
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```
4. Open the site at http://127.0.0.1:8000/ . Login uses the auth views in [`authentication/views.py`](authentication/views.py).

## Notes for contributors

- The project uses a custom user model defined in [`authentication/models.py`](authentication/models.py) and referenced by [`AUTH_USER_MODEL`](mabali_resort_management/settings.py).
- Dashboard pages render charts using scripts in [static/js/dashboards-analytics.js](static/js/dashboards-analytics.js). If you add new pages that need charts, follow the same pattern.
- Toast placement and disposal logic lives in [static/js/ui-toasts.js](static/js/ui-toasts.js).

## Tests

No application tests are included beyond the placeholder test modules:
- [authentication/tests.py](authentication/tests.py)
- [inventory/tests.py](inventory/tests.py)

Run Django tests with:
```sh
python manage.py test
```

## License

This repo contains sample/demo code. Add a LICENSE file if you intend to publish with an explicit license.
