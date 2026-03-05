from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0003_car_discount_and_photos'),
    ]

    operations = [
        # Remove old URL fields
        migrations.RemoveField(model_name='car', name='photo_url'),
        migrations.RemoveField(model_name='car', name='photo_url_2'),
        migrations.RemoveField(model_name='car', name='photo_url_3'),
        migrations.RemoveField(model_name='car', name='photo_url_4'),
        # Add new upload fields (photo already exists, add photo_2/3/4)
        migrations.AddField(
            model_name='car',
            name='photo_2',
            field=models.ImageField(blank=True, null=True, upload_to='cars/'),
        ),
        migrations.AddField(
            model_name='car',
            name='photo_3',
            field=models.ImageField(blank=True, null=True, upload_to='cars/'),
        ),
        migrations.AddField(
            model_name='car',
            name='photo_4',
            field=models.ImageField(blank=True, null=True, upload_to='cars/'),
        ),
    ]
