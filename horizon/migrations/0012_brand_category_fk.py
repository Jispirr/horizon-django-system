from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0011_inquiry_reply_thread'),
    ]

    operations = [
        # 1. Create Brand + Category tables
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(max_length=80, unique=True, blank=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(max_length=80, unique=True, blank=True)),
            ],
            options={'ordering': ['name'], 'verbose_name_plural': 'Categories'},
        ),
        # 2. Seed default data
        migrations.RunSQL(
            sql="""
            INSERT OR IGNORE INTO horizon_brand (name, slug) VALUES
              ('BMW',           'bmw'),
              ('Mercedes-Benz', 'mercedes-benz'),
              ('Toyota',        'toyota'),
              ('Tesla',         'tesla'),
              ('Porsche',       'porsche'),
              ('Lexus',         'lexus'),
              ('Foton',         'foton');
            INSERT OR IGNORE INTO horizon_category (name, slug) VALUES
              ('Sedan',     'sedan'),
              ('SUV',       'suv'),
              ('Sports',    'sports'),
              ('Electric',  'electric'),
              ('Truck',     'truck'),
              ('Van/MPV',   'van-mpv'),
              ('Crossover', 'crossover'),
              ('Pickup',    'pickup');
            """,
            reverse_sql="",
        ),
        # 3. Rebuild horizon_car with new FK columns replacing old char columns.
        #    SQLite does not support ALTER COLUMN so we do the standard
        #    create-new / copy / drop-old / rename dance entirely in SQL.
        migrations.RunSQL(
            sql="""
            CREATE TABLE "horizon_car_new" (
                "id"               integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "model"            varchar(100) NOT NULL,
                "year"             integer NOT NULL,
                "listing_type"     varchar(10) NOT NULL,
                "sale_price"       decimal(12, 2) NULL,
                "status"           varchar(20) NOT NULL,
                "mileage"          integer NULL,
                "transmission"     varchar(20) NOT NULL,
                "fuel_type"        varchar(20) NOT NULL,
                "color"            varchar(50) NOT NULL,
                "plate_number"     varchar(20) NOT NULL,
                "description"      text NOT NULL,
                "photo"            varchar(100) NULL,
                "photo_2"          varchar(100) NULL,
                "photo_3"          varchar(100) NULL,
                "photo_4"          varchar(100) NULL,
                "discount_percent" decimal(5, 2) NULL,
                "discount_label"   varchar(60) NOT NULL,
                "created_at"       datetime NOT NULL,
                "brand_id"         integer NULL REFERENCES "horizon_brand" ("id") DEFERRABLE INITIALLY DEFERRED,
                "category_id"      integer NULL REFERENCES "horizon_category" ("id") DEFERRABLE INITIALLY DEFERRED
            );
            INSERT INTO "horizon_car_new" (
                id, model, year, listing_type, sale_price, status, mileage,
                transmission, fuel_type, color, plate_number, description,
                photo, photo_2, photo_3, photo_4,
                discount_percent, discount_label, created_at,
                brand_id, category_id
            )
            SELECT
                c.id, c.model, c.year, c.listing_type, c.sale_price, c.status, c.mileage,
                c.transmission, c.fuel_type, c.color, c.plate_number, c.description,
                c.photo, c.photo_2, c.photo_3, c.photo_4,
                c.discount_percent, c.discount_label, c.created_at,
                (SELECT b.id FROM horizon_brand b WHERE b.slug = CASE c.brand
                    WHEN 'benz'     THEN 'mercedes-benz'
                    WHEN 'bmw'      THEN 'bmw'
                    WHEN 'toyota'   THEN 'toyota'
                    WHEN 'tesla'    THEN 'tesla'
                    WHEN 'porsche'  THEN 'porsche'
                    WHEN 'lexus'    THEN 'lexus'
                    WHEN 'foton'    THEN 'foton'
                    ELSE LOWER(c.brand)
                END),
                (SELECT cat.id FROM horizon_category cat WHERE cat.slug = CASE c.category
                    WHEN 'van'       THEN 'van-mpv'
                    WHEN 'sedan'     THEN 'sedan'
                    WHEN 'suv'       THEN 'suv'
                    WHEN 'sports'    THEN 'sports'
                    WHEN 'electric'  THEN 'electric'
                    WHEN 'truck'     THEN 'truck'
                    WHEN 'crossover' THEN 'crossover'
                    WHEN 'pickup'    THEN 'pickup'
                    ELSE LOWER(c.category)
                END)
            FROM horizon_car c;
            DROP TABLE "horizon_car";
            ALTER TABLE "horizon_car_new" RENAME TO "horizon_car";
            CREATE INDEX "horizon_car_brand_id" ON "horizon_car" ("brand_id");
            CREATE INDEX "horizon_car_category_id" ON "horizon_car" ("category_id");
            """,
            reverse_sql="",
        ),
        # 4. Update Django's migration state to match the new DB schema
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name='car', name='brand'),
                migrations.RemoveField(model_name='car', name='category'),
                migrations.AddField(
                    model_name='car',
                    name='brand',
                    field=models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='horizon.brand',
                    ),
                ),
                migrations.AddField(
                    model_name='car',
                    name='category',
                    field=models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='horizon.category',
                    ),
                ),
            ],
            database_operations=[],  # DB already updated by RunSQL above
        ),
    ]
