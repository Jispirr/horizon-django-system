from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0002_remove_car_rent_rate_alter_car_listing_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='photo_url_2',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='car',
            name='photo_url_3',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='car',
            name='photo_url_4',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='car',
            name='discount_percent',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True,
                help_text='Discount percentage (e.g. 20 for 20% off)'
            ),
        ),
        migrations.AddField(
            model_name='car',
            name='discount_label',
            field=models.CharField(
                blank=True, max_length=60,
                help_text="Short label shown on badge (e.g. 'Summer Sale')"
            ),
        ),
    ]
