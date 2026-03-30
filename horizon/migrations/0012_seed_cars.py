"""
Data migration — seeds the Car inventory with 21 vehicles (3 per brand).
Photos are copied from static/img/ into media/cars/ at migration time.
Safe to run multiple times: skips seeding if cars already exist.
"""

import os
import shutil
from pathlib import Path
from django.db import migrations


# ---------------------------------------------------------------------------
# Car seed data — 3 cars per brand, realistic PH-market specs & pricing
# ---------------------------------------------------------------------------
CARS = [
    # ── Toyota ──────────────────────────────────────────────────────────────
    {
        "brand": "toyota", "model": "Land Cruiser 300", "year": 2024,
        "category": "suv", "status": "available",
        "sale_price": 4990000,
        "mileage": 1200,
        "transmission": "automatic", "fuel_type": "diesel",
        "color": "Pearl White", "plate_number": "AAA 1234",
        "description": (
            "The all-new Land Cruiser 300 redefines luxury off-road capability. "
            "Powered by a twin-turbo V6 diesel engine producing 309 hp, it combines "
            "brute capability with a refined interior. Features include a 12.3-inch "
            "touchscreen, heated and ventilated seats, 360-degree camera, and Toyota's "
            "latest E-KDSS suspension. This unit is nearly new with only 1,200 km."
        ),
        "image_file": "img-toyota.png",
    },
    {
        "brand": "toyota", "model": "GR86", "year": 2023,
        "category": "sports", "status": "available",
        "sale_price": 2190000,
        "mileage": 8500,
        "transmission": "manual", "fuel_type": "gasoline",
        "color": "Ignition Red", "plate_number": "BBB 5678",
        "description": (
            "The second-generation GR86 raises the bar for affordable sports cars. "
            "A 2.4L naturally-aspirated flat-four produces 234 hp, paired with a "
            "slick 6-speed manual. Near-50/50 weight distribution and a revised "
            "chassis make this one of the most driver-focused cars at any price. "
            "Clean title, single owner, never tracked."
        ),
        "image_file": "img-toyota.png",
    },
    {
        "brand": "toyota", "model": "Hilux Conquest", "year": 2023,
        "category": "pickup", "status": "available",
        "sale_price": 1895000,
        "mileage": 22000,
        "transmission": "automatic", "fuel_type": "diesel",
        "color": "Grayish Blue Metallic", "plate_number": "CCC 9012",
        "description": (
            "Top-of-the-line Hilux Conquest with full leather interior, "
            "Apple CarPlay & Android Auto, 4x4 with locking rear differential, "
            "and Toyota Safety Sense suite. Built for both urban commuting and "
            "serious off-road adventures. Well-maintained with complete service records."
        ),
        "image_file": "img-toyota.png",
    },

    # ── BMW ─────────────────────────────────────────────────────────────────
    {
        "brand": "bmw", "model": "M3 Competition", "year": 2023,
        "category": "sedan", "status": "available",
        "sale_price": 8500000,
        "mileage": 5300,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Frozen Portimao Blue", "plate_number": "DDD 3456",
        "description": (
            "The G80 M3 Competition in the stunning Frozen Portimao Blue individual "
            "finish. The S58 3.0L twin-turbo straight-six delivers 510 hp and 650 Nm "
            "of torque, launching this four-door sports car to 100 km/h in 3.5 seconds. "
            "Equipped with M xDrive AWD, M Carbon bucket seats, ceramic brakes, "
            "and the full M Driver's Package. Low mileage, in immaculate condition."
        ),
        "image_file": "img-bmw.png",
        "discount_percent": 5,
        "discount_label": "5% Off — Limited Time",
    },
    {
        "brand": "bmw", "model": "X5 xDrive40i", "year": 2024,
        "category": "suv", "status": "available",
        "sale_price": 7200000,
        "mileage": 3100,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Sophisto Grey", "plate_number": "EEE 7890",
        "description": (
            "The F95 X5 xDrive40i pairs a 3.0L turbocharged straight-six (340 hp) "
            "with xDrive AWD for effortless performance in any condition. "
            "Panoramic sunroof, 4-zone climate control, Harman Kardon sound system, "
            "Driving Assistance Professional package, and massaging front seats. "
            "Near-new with full BMW warranty remaining."
        ),
        "image_file": "img-bmw.png",
    },
    {
        "brand": "bmw", "model": "320i Sport", "year": 2022,
        "category": "sedan", "status": "available",
        "sale_price": 3100000,
        "mileage": 31000,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Alpine White", "plate_number": "FFF 1234",
        "description": (
            "The G20 320i Sport — the benchmark executive sedan. A 2.0L TwinPower "
            "turbo produces 184 hp and pairs with an 8-speed Steptronic gearbox for "
            "smooth, efficient performance. Live Cockpit Professional with 12.3-inch "
            "digital dash, parking assistant, and Vernasca leather upholstery. "
            "Single owner, full dealer service history."
        ),
        "image_file": "img-bmw.png",
    },

    # ── Mercedes-Benz ────────────────────────────────────────────────────────
    {
        "brand": "benz", "model": "GLE 450 AMG Line", "year": 2024,
        "category": "suv", "status": "available",
        "sale_price": 9800000,
        "mileage": 2800,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Obsidian Black Metallic", "plate_number": "GGG 5678",
        "description": (
            "The GLE 450 in full AMG Line specification with the optional E-ACTIVE "
            "BODY CONTROL suspension — the smoothest ride in its class. "
            "The 3.0L inline-six mild hybrid makes 367 hp. Interior highlights include "
            "MBUX with dual 12.3-inch screens, Burmester 3D surround sound, "
            "heated/cooled/massaging seats, and a panoramic sliding sunroof. "
            "Showroom fresh, registered 2024."
        ),
        "image_file": "img-benz.png",
    },
    {
        "brand": "benz", "model": "C 200 Avantgarde", "year": 2023,
        "category": "sedan", "status": "available",
        "sale_price": 4650000,
        "mileage": 9800,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Manufaktur Diamond White Bright", "plate_number": "HHH 9012",
        "description": (
            "The W206 C-Class sets a new standard for compact luxury. "
            "A 2.0L turbocharged 4-cylinder EQ boost mild hybrid delivers 204 hp "
            "with surprising efficiency. The interior is a showcase of ambient lighting, "
            "a 11.9-inch portrait touchscreen, MBUX voice assistant, and the optional "
            "Energizing Comfort package. Single owner, immaculate inside and out."
        ),
        "image_file": "img-benz.png",
        "discount_percent": 3,
        "discount_label": "3% Loyalty Discount",
    },
    {
        "brand": "benz", "model": "G 63 AMG", "year": 2023,
        "category": "suv", "status": "reserved",
        "sale_price": 22500000,
        "mileage": 4100,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Designo Night Black Magno", "plate_number": "III 3456",
        "description": (
            "The legendary G-Wagen in full AMG 63 trim. The hand-built AMG 4.0L "
            "twin-turbo V8 produces 585 hp and 850 Nm, with an exhaust note that "
            "commands attention on any road. Three locking differentials, fully "
            "independent AMG RIDE CONTROL+ air suspension, Nappa leather with "
            "AMG Performance seats, and a 1590-watt Burmester high-end surround system. "
            "One of the most iconic SUVs ever built."
        ),
        "image_file": "img-benz.png",
    },

    # ── Tesla ────────────────────────────────────────────────────────────────
    {
        "brand": "tesla", "model": "Model S Plaid", "year": 2023,
        "category": "sedan", "status": "available",
        "sale_price": 12000000,
        "mileage": 6200,
        "transmission": "automatic", "fuel_type": "electric",
        "color": "Midnight Silver Metallic", "plate_number": "JJJ 7890",
        "description": (
            "The Model S Plaid is the fastest production sedan ever made. "
            "Three motors, 1,020 hp, 0-100 km/h in 2.1 seconds, and a real-world "
            "range of over 600 km. The 17-inch landscape touchscreen controls everything, "
            "and the yoke steering wheel gives a futuristic feel. Over-the-air updates "
            "keep this car current indefinitely. This unit has Autopilot and Full "
            "Self-Driving capability included."
        ),
        "image_file": "img-tesla.png",
    },
    {
        "brand": "tesla", "model": "Model 3 Long Range AWD", "year": 2023,
        "category": "sedan", "status": "available",
        "sale_price": 3850000,
        "mileage": 15400,
        "transmission": "automatic", "fuel_type": "electric",
        "color": "Deep Blue Metallic", "plate_number": "KKK 1234",
        "description": (
            "The most popular electric car in the world, and for good reason. "
            "Dual-motor AWD delivers 358 hp and a range of 580+ km on a single charge. "
            "The minimalist 15.4-inch touchscreen runs navigation, media, and all "
            "vehicle controls. Tesla's Autopilot comes standard, with the option to "
            "upgrade to Full Self-Driving. One careful owner, home-charged only."
        ),
        "image_file": "img-tesla.png",
        "discount_percent": 4,
        "discount_label": "Year-End Clearance",
    },
    {
        "brand": "tesla", "model": "Model X Long Range", "year": 2022,
        "category": "suv", "status": "available",
        "sale_price": 8900000,
        "mileage": 28000,
        "transmission": "automatic", "fuel_type": "electric",
        "color": "Pearl White Multi-Coat", "plate_number": "LLL 5678",
        "description": (
            "The Model X Long Range with the iconic Falcon Wing doors and seating "
            "for up to seven. Dual-motor AWD, 670 hp, and a 580 km range make this "
            "the most capable electric SUV on the market. Comes with full entertainment "
            "package, premium audio, heated/cooled seats on all three rows, "
            "and the 17-inch horizontal touchscreen. Clean title, complete charging kit."
        ),
        "image_file": "img-tesla.png",
    },

    # ── Porsche ──────────────────────────────────────────────────────────────
    {
        "brand": "porsche", "model": "911 Carrera GTS", "year": 2024,
        "category": "sports", "status": "available",
        "sale_price": 18500000,
        "mileage": 1800,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Python Green Metallic", "plate_number": "MMM 9012",
        "description": (
            "The 992-generation 911 GTS represents the sweet spot of the 911 range. "
            "A 3.0L twin-turbo flat-six making 480 hp in a rear-wheel-drive chassis "
            "gives a driving experience nothing else can replicate. This example has "
            "the Sport Chrono Package, PCCB ceramic composite brakes, Burmester sound, "
            "full bucket seats in leather, and the exclusive Python Green Metallic paint "
            "from the Porsche Paint to Sample program. Essentially new."
        ),
        "image_file": "img-porsche.png",
    },
    {
        "brand": "porsche", "model": "Cayenne Turbo GT", "year": 2023,
        "category": "suv", "status": "available",
        "sale_price": 24000000,
        "mileage": 7600,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Frozen Blue Metallic", "plate_number": "NNN 3456",
        "description": (
            "The Cayenne Turbo GT — the fastest production SUV on the Nürburgring. "
            "A 4.0L twin-turbo V8 makes 640 hp, launching this SUV to 100 km/h "
            "in 3.3 seconds. Adaptive air suspension with PDCC Sport anti-roll system, "
            "carbon-ceramic brakes, fixed-back carbon bucket seats, and Porsche Torque "
            "Vectoring Plus. A track car that seats five and swallows luggage."
        ),
        "image_file": "img-porsche.png",
        "discount_percent": 2,
        "discount_label": "2% Off — Demo Unit",
    },
    {
        "brand": "porsche", "model": "Macan S", "year": 2023,
        "category": "suv", "status": "available",
        "sale_price": 5800000,
        "mileage": 17200,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Carmine Red", "plate_number": "OOO 7890",
        "description": (
            "The Macan S is the entry point into Porsche SUV ownership — and it "
            "drives unlike anything else in its class. A 2.9L twin-turbo V6 makes "
            "380 hp, channelled through PDK and Porsche Traction Management AWD. "
            "Sport Chrono Package, BOSE surround sound, SportDesign steering wheel, "
            "and the stunning Carmine Red paint. Single female owner, garaged."
        ),
        "image_file": "img-porsche.png",
    },

    # ── Lexus ────────────────────────────────────────────────────────────────
    {
        "brand": "lexus", "model": "LX 600 F Sport", "year": 2024,
        "category": "suv", "status": "available",
        "sale_price": 11500000,
        "mileage": 4500,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Sonic Titanium", "plate_number": "PPP 1234",
        "description": (
            "The LX 600 F Sport is Lexus's flagship SUV in its most driver-focused "
            "trim. A 3.5L twin-turbo V6 makes 409 hp, paired with a 10-speed automatic "
            "and full-time 4WD with multi-terrain select. The F Sport trim adds "
            "adaptive variable suspension, sport-tuned steering, 22-inch F Sport "
            "wheels, and a bold mesh grille. Mark Levinson 25-speaker audio, "
            "semi-aniline leather, and a massive panoramic roof complete the package."
        ),
        "image_file": "img-lexus.png",
    },
    {
        "brand": "lexus", "model": "IS 500 F Sport Performance", "year": 2023,
        "category": "sedan", "status": "available",
        "sale_price": 6200000,
        "mileage": 11300,
        "transmission": "automatic", "fuel_type": "gasoline",
        "color": "Obsidian", "plate_number": "QQQ 5678",
        "description": (
            "The IS 500 F Sport Performance brings back the V8 to the sports sedan "
            "segment. A naturally-aspirated 5.0L V8 makes 472 hp and revs to 7,300 rpm "
            "with an intoxicating soundtrack. Brembo front brakes, Torsen limited-slip "
            "differential, AVS adaptive suspension, and exclusive 19-inch forged wheels. "
            "This is the last great naturally-aspirated sports sedan."
        ),
        "image_file": "img-lexus.png",
    },
    {
        "brand": "lexus", "model": "RX 500h F Sport+", "year": 2023,
        "category": "suv", "status": "available",
        "sale_price": 5450000,
        "mileage": 19800,
        "transmission": "automatic", "fuel_type": "hybrid",
        "color": "Nori Green Pearl", "plate_number": "RRR 9012",
        "description": (
            "The all-new RX 500h F Sport+ uses a 2.4L turbo four-cylinder hybrid "
            "system producing a combined 371 hp with DIRECT4 AWD torque vectoring. "
            "The result is a genuine 6.0-second 0-100 time alongside 11 L/100 km "
            "fuel economy. 14-inch touchscreen, Mark Levinson audio, panoramic roof, "
            "and a stunning Nori Green Pearl paint that shifts colour in different light."
        ),
        "image_file": "img-lexus.png",
        "discount_percent": 3,
        "discount_label": "3% Fleet Discount",
    },

    # ── Foton ────────────────────────────────────────────────────────────────
    {
        "brand": "foton", "model": "Toplander 4x4 AT", "year": 2023,
        "category": "suv", "status": "available",
        "sale_price": 1295000,
        "mileage": 14200,
        "transmission": "automatic", "fuel_type": "diesel",
        "color": "Ivory White", "plate_number": "SSS 3456",
        "description": (
            "The Foton Toplander 4x4 AT is the best-value seven-seat SUV on the "
            "Philippine market. A 2.0L turbocharged diesel makes 150 hp and 350 Nm, "
            "paired with a 6-speed automatic and 4WD with 2H/4H/4L modes. "
            "Leather seats for all three rows, 10-inch touchscreen, reverse camera, "
            "and a 3-year Foton warranty. Perfect for families who need space and "
            "occasional off-road capability without the luxury price tag."
        ),
        "image_file": "img-foton.png",
    },
    {
        "brand": "foton", "model": "Thunder 4x4 Superior", "year": 2024,
        "category": "pickup", "status": "available",
        "sale_price": 1098000,
        "mileage": 3200,
        "transmission": "manual", "fuel_type": "diesel",
        "color": "Meteor Gray", "plate_number": "TTT 7890",
        "description": (
            "The Foton Thunder Superior is a seriously capable workhorse pickup at "
            "an unbeatable price. The 2.8L turbodiesel puts out 150 hp and 350 Nm, "
            "and the 4WD system handles everything from farm tracks to mountain roads. "
            "Hard tri-fold bed cover, roll bar, LED light bar, chrome sports bar, "
            "and a 7-inch infotainment system. Near-new with only 3,200 km."
        ),
        "image_file": "img-foton.png",
    },
    {
        "brand": "foton", "model": "View Transvan 2.8", "year": 2022,
        "category": "van", "status": "available",
        "sale_price": 895000,
        "mileage": 38000,
        "transmission": "manual", "fuel_type": "diesel",
        "color": "Silver Metallic", "plate_number": "UUU 1234",
        "description": (
            "The Foton View Transvan seats up to 18 passengers in a well-appointed "
            "interior with individual reading lights and ventilation controls. "
            "The 2.8L diesel is frugal at highway speeds and easy to maintain. "
            "Often used as a shuttle or company transport vehicle. This unit has been "
            "professionally maintained with complete service records available. "
            "Ideal for businesses, schools, or large families."
        ),
        "image_file": "img-foton.png",
    },
]


def seed_cars(apps, schema_editor):
    Car = apps.get_model("horizon", "Car")

    # Skip if cars already seeded
    if Car.objects.exists():
        return

    # Resolve paths
    this_file = Path(__file__).resolve()
    base_dir = this_file.parents[3]          # …/horizon_fixed_v9/
    static_img = base_dir / "static" / "img"
    media_cars = base_dir / "media" / "cars"
    media_cars.mkdir(parents=True, exist_ok=True)

    for data in CARS:
        # Copy image into media/cars/ if source exists
        photo_field = ""
        src = static_img / data["image_file"]
        if src.exists():
            # Use brand-specific name to avoid collisions
            brand = data["brand"]
            dest_name = f"seed_{brand}.png"
            dest = media_cars / dest_name
            if not dest.exists():
                shutil.copy2(str(src), str(dest))
            photo_field = f"cars/{dest_name}"

        Car.objects.create(
            brand=data["brand"],
            model=data["model"],
            year=data["year"],
            category=data["category"],
            status=data["status"],
            sale_price=data["sale_price"],
            mileage=data.get("mileage"),
            transmission=data["transmission"],
            fuel_type=data["fuel_type"],
            color=data["color"],
            plate_number=data["plate_number"],
            description=data["description"],
            photo=photo_field,
            discount_percent=data.get("discount_percent"),
            discount_label=data.get("discount_label", ""),
        )


def unseed_cars(apps, schema_editor):
    """Reverse: remove only the seeded cars (by known plate numbers)."""
    Car = apps.get_model("horizon", "Car")
    plates = [c["plate_number"] for c in CARS]
    Car.objects.filter(plate_number__in=plates).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("horizon", "0011_inquiry_reply_thread"),
    ]

    operations = [
        migrations.RunPython(seed_cars, reverse_code=unseed_cars),
    ]
