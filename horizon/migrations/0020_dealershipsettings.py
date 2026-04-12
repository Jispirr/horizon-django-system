from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0019_customerreview_is_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='DealershipSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dealership_name', models.CharField(default='Horizon Car Dealership', max_length=120)),
                ('phone', models.CharField(default='+63 (2) 8123-4567', max_length=40)),
                ('email', models.EmailField(default='info@horizonauto.com')),
                ('address', models.CharField(default='123 Horizon Drive, Quezon City, Metro Manila', max_length=200)),
                ('weekday_hours', models.CharField(default='8:00 AM \u2013 7:00 PM', max_length=60)),
                ('weekend_hours', models.CharField(default='10:00 AM \u2013 5:00 PM', max_length=60)),
                ('facebook_url', models.URLField(blank=True, default='')),
                ('instagram_url', models.URLField(blank=True, default='')),
                ('telegram_url', models.URLField(blank=True, default='')),
                ('tagline', models.CharField(blank=True, default='', max_length=200)),
            ],
            options={
                'verbose_name': 'Dealership Settings',
                'verbose_name_plural': 'Dealership Settings',
            },
        ),
    ]
