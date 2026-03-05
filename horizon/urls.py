from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),

    # Admin panel
    path('admin-panel/login/', views.admin_login, name='admin_login'),
    path('admin-panel/logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),

    # Cars CRUD
    path('admin-panel/cars/', views.admin_cars, name='admin_cars'),
    path('admin-panel/cars/add/', views.admin_car_add, name='admin_car_add'),
    path('admin-panel/cars/<int:pk>/edit/', views.admin_car_edit, name='admin_car_edit'),
    path('admin-panel/cars/<int:pk>/delete/', views.admin_car_delete, name='admin_car_delete'),

    # Orders
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/add/', views.admin_order_add, name='admin_order_add'),
    path('admin-panel/orders/<int:pk>/edit/', views.admin_order_edit, name='admin_order_edit'),

    # Customers
    path('admin-panel/customers/', views.admin_customers, name='admin_customers'),
    path('admin-panel/customers/add/', views.admin_customer_add, name='admin_customer_add'),

    # Inquiries
    path('admin-panel/inquiries/', views.admin_inquiries, name='admin_inquiries'),
    path('admin-panel/inquiries/<int:pk>/delete/', views.admin_inquiry_delete, name='admin_inquiry_delete'),

    # Settings
    path('admin-panel/settings/', views.admin_settings, name='admin_settings'),
    path('admin-panel/discounts/', views.admin_discounts, name='admin_discounts'),
]
