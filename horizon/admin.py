from django.contrib import admin
from .models import Brand, Category, Car, Customer, SaleOrder, Inquiry, CustomerReview, TestDriveRequest

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

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

@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display  = ['customer_name', 'vehicle_purchased', 'rating', 'date_submitted', 'is_approved']
    list_filter   = ['rating', 'is_approved']
    search_fields = ['customer_name', 'vehicle_purchased', 'review_text']
    list_editable = ['is_approved']
    ordering      = ['-date_submitted']

@admin.register(TestDriveRequest)
class TestDriveRequestAdmin(admin.ModelAdmin):
    list_display  = ['ref_number', 'full_name', 'phone', 'car', 'preferred_date', 'preferred_time', 'status', 'created_at']
    list_filter   = ['status', 'preferred_date']
    search_fields = ['first_name', 'last_name', 'phone']
    list_editable = ['status']
    ordering      = ['-created_at']
