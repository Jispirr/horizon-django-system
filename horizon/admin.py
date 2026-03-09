from django.contrib import admin
from .models import Car, Customer, SaleOrder, Inquiry

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'brand', 'category', 'listing_type', 'status', 'sale_price']
    list_filter = ['brand', 'category', 'listing_type', 'status']
    search_fields = ['model', 'plate_number', 'color']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'customer_type']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(SaleOrder)
class SaleOrderAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'customer', 'car', 'amount', 'status', 'date']
    list_filter = ['status', 'payment_method']

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'vehicle_interest', 'created_at', 'is_read']
    list_filter = ['is_read', 'vehicle_interest']