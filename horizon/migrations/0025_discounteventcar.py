from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0024_dealershipsettings_footer_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='discountevent',
            name='description',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.CreateModel(
            name='DiscountEventCar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount_percent', models.DecimalField(decimal_places=2, max_digits=5)),
                ('discount_label', models.CharField(blank=True, max_length=60)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_cars', to='horizon.discountevent')),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_discounts', to='horizon.car')),
            ],
            options={
                'ordering': ['car__brand__name', 'car__model'],
                'unique_together': {('event', 'car')},
            },
        ),
    ]
