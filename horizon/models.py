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
    LISTING_CHOICES = [('sale', 'For Sale')]
    STATUS_CHOICES  = [('available', 'Available'), ('reserved', 'Reserved'), ('sold', 'Sold')]
    TRANSMISSION_CHOICES = [('automatic', 'Automatic'), ('manual', 'Manual'), ('cvt', 'CVT')]
    FUEL_CHOICES = [('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')]

    brand        = models.CharField(max_length=20, choices=BRAND_CHOICES)
    model        = models.CharField(max_length=100)
    year         = models.IntegerField()
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    listing_type = models.CharField(max_length=10, choices=LISTING_CHOICES, default='sale')
    sale_price   = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    mileage      = models.IntegerField(null=True, blank=True)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default='automatic')
    fuel_type    = models.CharField(max_length=20, choices=FUEL_CHOICES, default='gasoline')
    color        = models.CharField(max_length=50, blank=True)
    plate_number = models.CharField(max_length=20, blank=True)
    description  = models.TextField(blank=True)

    photo   = models.ImageField(upload_to='cars/', null=True, blank=True)
    photo_2 = models.ImageField(upload_to='cars/', null=True, blank=True)
    photo_3 = models.ImageField(upload_to='cars/', null=True, blank=True)
    photo_4 = models.ImageField(upload_to='cars/', null=True, blank=True)

    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_label   = models.CharField(max_length=60, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.year} {self.get_brand_display()} {self.model}"

    def get_display_image(self):
        return self.photo.url if self.photo else None

    def get_all_photos(self):
        return [f.url for f in [self.photo, self.photo_2, self.photo_3, self.photo_4] if f]

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
    first_name    = models.CharField(max_length=50)
    last_name     = models.CharField(max_length=50)
    email         = models.EmailField(unique=True)
    phone         = models.CharField(max_length=20)
    customer_type = models.CharField(max_length=10, default='buyer')
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class SaleOrder(models.Model):
    STATUS_CHOICES  = [('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')]
    PAYMENT_CHOICES = [('cash', 'Cash'), ('bank', 'Bank Financing'), ('inhouse', 'In-house')]

    customer       = models.ForeignKey(Customer, on_delete=models.PROTECT)
    car            = models.ForeignKey(Car, on_delete=models.PROTECT)
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date           = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk:05d} - {self.customer}"


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ('new',        'New'),
        ('processing', 'Processing'),
        ('resolved',   'Resolved'),
    ]
    first_name       = models.CharField(max_length=50)
    last_name        = models.CharField(max_length=50)
    email            = models.EmailField()
    phone            = models.CharField(max_length=20, blank=True)
    vehicle_interest = models.CharField(max_length=50, blank=True)
    car              = models.ForeignKey('Car', null=True, blank=True, on_delete=models.SET_NULL, related_name='inquiries')
    message          = models.TextField()
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes      = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    is_read          = models.BooleanField(default=False)

    def __str__(self):
        return f"Inquiry from {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class DiscountEvent(models.Model):
    name            = models.CharField(max_length=80)
    description     = models.CharField(max_length=160, blank=True)
    is_active       = models.BooleanField(default=False)
    banner_title    = models.CharField(max_length=60, blank=True)
    banner_subtitle = models.CharField(max_length=120, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{'[ON] ' if self.is_active else '[OFF] '}{self.name}"

    def save(self, *args, **kwargs):
        if self.is_active:
            DiscountEvent.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-is_active', '-created_at']


class ChatSession(models.Model):
    """A ticket-based live chat session started from the website widget."""
    STATUS_CHOICES = [
        ('open',       'Open'),
        ('in_progress','In Progress'),
        ('resolved',   'Resolved'),
        ('closed',     'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('normal', 'Normal'),
        ('high',   'High'),
    ]

    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    subject       = models.CharField(max_length=200, blank=True)
    name          = models.CharField(max_length=100)
    email         = models.EmailField()
    token         = models.CharField(max_length=64, unique=True)
    status        = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    priority      = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    is_read       = models.BooleanField(default=False)
    admin_notes   = models.TextField(blank=True)
    started_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ticket_number} — {self.name}"

    def save(self, *args, **kwargs):
        import secrets
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.ticket_number:
            # Generate ticket number after save to get PK
            super().save(*args, **kwargs)
            self.ticket_number = f'CHT-{self.pk:05d}'
            ChatSession.objects.filter(pk=self.pk).update(ticket_number=self.ticket_number)
            return
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.name

    @property
    def initials(self):
        parts = self.name.strip().split()
        return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    @property
    def unread_count(self):
        return self.messages.filter(sender='visitor', is_seen=False).count()

    @property
    def last_message(self):
        return self.messages.last()

    class Meta:
        ordering = ['-updated_at']


class ChatMessage(models.Model):
    """A single message in a chat session."""
    SENDER_CHOICES = [('visitor', 'Visitor'), ('admin', 'Admin')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender  = models.CharField(max_length=10, choices=SENDER_CHOICES)
    body    = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"[{self.sender}] {self.session} @ {self.sent_at:%H:%M}"
