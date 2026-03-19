from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0004_car_photo_fields_to_upload'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, help_text='e.g. Summer Sale, Flash Deal')),
                ('description', models.CharField(max_length=160, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('banner_title', models.CharField(max_length=60, blank=True)),
                ('banner_subtitle', models.CharField(max_length=120, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-is_active', '-created_at']},
        ),
    ]
