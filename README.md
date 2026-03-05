# Horizon Car Dealership — Django Project

## Project Structure
```
horizon_django/
├── manage.py
├── requirements.txt
├── db.sqlite3              (created after migrations)
├── horizon_project/        (Django settings & URLs)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── horizon/                (Main app)
    ├── models.py           (Car, Customer, SaleOrder, RentalBooking, Inquiry)
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── static/
    │   ├── css/stylesheet.css
    │   ├── js/javarice.js
    │   ├── img/            (all brand logos + homepage image)
    │   └── fonts/          (Horizon, Poppins fonts)
    └── templates/horizon/
        ├── base.html           (public base)
        ├── index.html          (homepage)
        ├── catalog.html        (car catalog with filters)
        ├── admin_base.html     (admin sidebar layout)
        ├── admin_login.html
        ├── admin_dashboard.html
        ├── admin_cars.html
        ├── admin_car_form.html (add/edit)
        ├── admin_orders.html
        ├── admin_order_form.html
        ├── admin_order_edit.html
        ├── admin_rentals.html
        ├── admin_rental_form.html
        ├── admin_rental_edit.html
        ├── admin_customers.html
        ├── admin_customer_form.html
        ├── admin_inquiries.html
        └── admin_settings.html
```

## Setup Instructions

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create a superuser (admin account)
```bash
python manage.py createsuperuser
```
Follow the prompts to set a username and password.

### 4. Run the development server
```bash
python manage.py runserver
```

### 5. Open in browser
- **Homepage:** http://127.0.0.1:8000/
- **Catalog:** http://127.0.0.1:8000/catalog/
- **Admin Panel:** http://127.0.0.1:8000/admin-panel/
- **Django Admin:** http://127.0.0.1:8000/django-admin/

## URL Overview

| URL | Description |
|-----|-------------|
| `/` | Homepage with carousel, about, contact |
| `/catalog/` | Car catalog with brand/category/year filters |
| `/contact/submit/` | Contact form POST endpoint |
| `/admin-panel/` | Custom admin dashboard |
| `/admin-panel/login/` | Admin login page |
| `/admin-panel/cars/` | Cars inventory |
| `/admin-panel/cars/add/` | Add new car |
| `/admin-panel/orders/` | Sale orders |
| `/admin-panel/rentals/` | Rental bookings |
| `/admin-panel/customers/` | Customer list |
| `/admin-panel/inquiries/` | Contact form submissions |
| `/admin-panel/settings/` | Settings page |
| `/django-admin/` | Django built-in admin |

## Key Features
- **Public site** — Homepage, brand carousel, about section, contact form (saves to DB)
- **Catalog** — Server-side filtering by brand, category, and year
- **Admin panel** — Full CRUD for cars, orders, rentals, customers, inquiries
- **Authentication** — Staff-only access to admin panel
- **Database** — SQLite (easy to switch to PostgreSQL in settings.py)
