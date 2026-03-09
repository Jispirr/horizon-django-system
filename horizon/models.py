from django.db import models


class Car(models.Model):
    BRAND_CHOICES = [
        ('bmw', 'BMW'),
        ('benz', 'Mercedes-Benz'),
        ('toyota', 'Toyota'),
        ('tesla', 'Tesla'),
        ('porsche', 'Porsche'),
        ('lexus', 'Lexus'),
        ('foton', 'Foton'),
    ]
    CATEGORY_CHOICES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('sports', 'Sports'),
        ('electric', 'Electric'),
        ('truck', 'Truck'),
        ('van', 'Van/MPV'),
        ('crossover', 'Crossover'),
        ('pickup', 'Pickup'),
    ]
    LISTING_CHOICES = [
        ('sale', 'For Sale'),
    ]
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
    ]
    TRANSMISSION_CHOICES = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('cvt', 'CVT'),
    ]
    FUEL_CHOICES = [
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ]

    brand           = models.CharField(max_length=20, choices=BRAND_CHOICES)
    model           = models.CharField(max_length=100)
    year            = models.IntegerField()
    category        = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    listing_type    = models.CharField(max_length=10, choices=LISTING_CHOICES, default='sale')
    sale_price      = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    mileage         = models.IntegerField(null=True, blank=True)
    transmission    = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='automatic')
    fuel_type       = models.CharField(max_length=20, choices=FUEL_CHOICES, default='gasoline')
    color           = models.CharField(max_length=50, blank=True)
    plate_number    = models.CharField(max_length=20, blank=True)
    description     = models.TextField(blank=True)

    # File uploads
    photo   = models.ImageField(upload_to='cars/', null=True, blank=True)
    photo_2 = models.ImageField(upload_to='cars/', null=True, blank=True)
    photo_3 = models.ImageField(upload_to='cars/', null=True, blank=True)
    photo_4 = models.ImageField(upload_to='cars/', null=True, blank=True)

    # Discount
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                           help_text='Discount percentage (e.g. 20 for 20% off)')
    discount_label   = models.CharField(max_length=60, blank=True,
                                        help_text="Short label shown on badge (e.g. 'Summer Sale')")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.year} {self.get_brand_display()} {self.model}"

    def get_display_image(self):
        if self.photo:
            return self.photo.url
        return None

    def get_all_photos(self):
        photos = []
        for field in [self.photo, self.photo_2, self.photo_3, self.photo_4]:
            if field:
                photos.append(field.url)
        return photos

    @property
    def discounted_price(self):
        if self.sale_price and self.discount_percent:
            from decimal import Decimal
            return self.sale_price * (1 - self.discount_percent / Decimal('100'))
        return None

    @property
    def has_discount(self):
        return bool(self.discount_percent and self.discount_percent > 0)


class Customer(models.Model):
    TYPE_CHOICES = [
        ('buyer', 'Buyer'),
    ]
    first_name    = models.CharField(max_length=50)
    last_name     = models.CharField(max_length=50)
    email         = models.EmailField(unique=True)
    phone         = models.CharField(max_length=20)
    customer_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='buyer')
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class SaleOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank Financing'),
        ('inhouse', 'In-house'),
    ]
    customer       = models.ForeignKey(Customer, on_delete=models.PROTECT)
    car            = models.ForeignKey(Car, on_delete=models.PROTECT)
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date           = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk:05d} - {self.customer}"


class Inquiry(models.Model):
    first_name       = models.CharField(max_length=50)
    last_name        = models.CharField(max_length=50)
    email            = models.EmailField()
    phone            = models.CharField(max_length=20, blank=True)
    vehicle_interest = models.CharField(max_length=50, blank=True)
    message          = models.TextField()
    created_at       = models.DateTimeField(auto_now_add=True)
    is_read          = models.BooleanField(default=False)

    def __str__(self):
        return f"Inquiry from {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"