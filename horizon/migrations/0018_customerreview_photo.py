from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0017_customerreview_car_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerreview',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='reviews/'),
        ),
        migrations.AddField(
            model_name='customerreview',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
    ]
