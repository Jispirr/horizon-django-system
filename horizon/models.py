from django.db import models
from django.utils.text import slugify
import os
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image as PilImage


def _compress_image(field, max_w=1200, max_h=900, quality=82):
    """Resize and compress an ImageField in-place. Converts PNG→JPEG when safe."""
    if not field:
        return
    try:
        field.open('rb')
        img = PilImage.open(field)
        original_format = img.format or 'JPEG'

        # Convert palette/transparency modes before resizing
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGBA')
            # Keep as PNG to preserve transparency
            save_format = 'PNG'
            ext = '.png'
        else:
            img = img.convert('RGB')
            save_format = 'JPEG'
            ext = '.jpg'

        # Resize only if larger than max dimensions
        if img.width > max_w or img.height > max_h:
            img.thumbnail((max_w, max_h), PilImage.LANCZOS)

        buffer = BytesIO()
        if save_format == 'PNG':
            img.save(buffer, format='PNG', optimize=True)
        else:
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)

        base = os.path.splitext(os.path.basename(field.name))[0]
        field.save(base + ext, ContentFile(buffer.read()), save=False)
    except Exception:
        pass  # Never break a save due to image processing


class Brand(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        _compress_image(self.logo, max_w=400, max_h=400, quality=85)
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    icon = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        _compress_image(self.icon, max_w=200, max_h=200, quality=85)
        super().save(*args, **kwargs)


class Car(models.Model):
    LISTING_CHOICES = [('sale', 'For Sale')]
    STATUS_CHOICES  = [('available', 'Available'), ('reserved', 'Reserved'), ('sold', 'Sold')]
    TRANSMISSION_CHOICES = [('automatic', 'Automatic'), ('manual', 'Manual'), ('cvt', 'CVT')]
    FUEL_CHOICES = [('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')]

    brand        = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True, blank=True)
    model        = models.CharField(max_length=100)
    year         = models.IntegerField()
    category     = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)
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
        brand_name = self.brand.name if self.brand else '—'
        return f"{self.year} {brand_name} {self.model}"

    def get_brand_display(self):
        return self.brand.name if self.brand else '—'

    def get_category_display(self):
        return self.category.name if self.category else '—'

    @property
    def brand_slug(self):
        return self.brand.slug if self.brand else ''

    @property
    def category_slug(self):
        return self.category.slug if self.category else ''

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
    def discount_savings(self):
        if self.sale_price and self.discount_percent:
            from decimal import Decimal
            return self.sale_price * (self.discount_percent / Decimal('100'))
        return None

    @property
    def has_discount(self):
        return bool(self.discount_percent and self.discount_percent > 0)

    def save(self, *args, **kwargs):
        for field in [self.photo, self.photo_2, self.photo_3, self.photo_4]:
            _compress_image(field, max_w=1200, max_h=900, quality=82)
        super().save(*args, **kwargs)


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

    reply_token = models.CharField(max_length=64, blank=True, unique=True, null=True)

    def __str__(self):
        return f"Inquiry from {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def inquiry_number(self):
        return f"INQ-{self.pk:05d}"

    def save(self, *args, **kwargs):
        if not self.reply_token:
            import secrets
            self.reply_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class InquiryReply(models.Model):
    SENDER_CHOICES = [('visitor', 'Visitor'), ('admin', 'Admin')]

    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='replies')
    sender  = models.CharField(max_length=10, choices=SENDER_CHOICES)
    body    = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"[{self.sender}] {self.inquiry} @ {self.sent_at:%H:%M}"


class DiscountEvent(models.Model):
    name            = models.CharField(max_length=80)
    description     = models.CharField(max_length=160, blank=True)
    is_active       = models.BooleanField(default=False)
    banner_title    = models.CharField(max_length=60, blank=True)
    banner_subtitle = models.CharField(max_length=120, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    cars            = models.ManyToManyField('Car', blank=True, related_name='events')

    def __str__(self):
        return f"{'[ON] ' if self.is_active else '[OFF] '}{self.name}"

    def save(self, *args, **kwargs):
        if self.is_active:
            DiscountEvent.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-is_active', '-created_at']


class ChatSession(models.Model):
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


class CustomerReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    customer_name     = models.CharField(max_length=100)
    vehicle_purchased = models.CharField(max_length=150)
    car               = models.ForeignKey('Car', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviews')
    rating            = models.IntegerField(choices=RATING_CHOICES, default=5)
    review_text       = models.TextField()
    photo             = models.ImageField(upload_to='reviews/', null=True, blank=True)
    date_submitted    = models.DateTimeField(auto_now_add=True)
    is_approved       = models.BooleanField(default=False)
    is_verified       = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_submitted']

    def __str__(self):
        return f"{self.customer_name} — {self.vehicle_purchased} ({self.rating}★)"

    @property
    def star_range(self):
        return range(1, 6)

    def save(self, *args, **kwargs):
        _compress_image(self.photo, max_w=600, max_h=600, quality=82)
        super().save(*args, **kwargs)


class ChatMessage(models.Model):
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


class DealershipSettings(models.Model):
    """Singleton model for dealership-wide settings."""
    dealership_name  = models.CharField(max_length=120, default='Horizon Car Dealership')
    phone            = models.CharField(max_length=40,  default='+63 (2) 8123-4567')
    email            = models.EmailField(default='info@horizonauto.com')
    address          = models.CharField(max_length=200, default='123 Horizon Drive, Quezon City, Metro Manila')
    weekday_hours    = models.CharField(max_length=60,  default='8:00 AM – 7:00 PM')
    weekend_hours    = models.CharField(max_length=60,  default='10:00 AM – 5:00 PM')
    facebook_url     = models.URLField(blank=True, default='')
    instagram_url    = models.URLField(blank=True, default='')
    telegram_url     = models.URLField(blank=True, default='')
    tagline          = models.CharField(max_length=200, blank=True, default='')
    brand_name       = models.CharField(max_length=40, default='HORIZON',
                           help_text='Short name shown in the navbar (e.g. HORIZON)')
    chat_avatar_letter = models.CharField(max_length=2, default='H',
                           help_text='1-2 letter initial shown in the chat widget avatar')
    footer_tagline   = models.CharField(max_length=200, blank=True,
                           default='Premium vehicles, exceptional service. Your trusted dealership in Metro Manila.',
                           help_text='Short description shown under the brand name in the footer')
    footer_copyright = models.CharField(max_length=200, blank=True, default='',
                           help_text='Custom copyright line. Leave blank to auto-generate from dealership name.')
    footer_show_nav      = models.BooleanField(default=True, help_text='Show the Navigate links column')
    footer_show_services = models.BooleanField(default=True, help_text='Show the Services links column')
    footer_show_contact  = models.BooleanField(default=True, help_text='Show the Contact details column')
    footer_show_socials  = models.BooleanField(default=True, help_text='Show social media icon links')

    class Meta:
        verbose_name = verbose_name_plural = 'Dealership Settings'

    def __str__(self):
        return self.dealership_name

    @classmethod
    def get(cls):
        """Return the singleton instance, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class TestDriveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    car          = models.ForeignKey('Car', on_delete=models.SET_NULL, null=True, blank=True, related_name='test_drives')
    first_name   = models.CharField(max_length=50)
    last_name    = models.CharField(max_length=50, blank=True)
    phone        = models.CharField(max_length=20)
    preferred_date = models.DateField()
    preferred_time = models.CharField(max_length=10, blank=True)
    notes        = models.TextField(blank=True)
    status       = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    admin_notes  = models.TextField(blank=True)
    is_read      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TD-{self.pk:05d} — {self.first_name} {self.last_name} ({self.preferred_date})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def ref_number(self):
        return f"TD-{self.pk:05d}"
