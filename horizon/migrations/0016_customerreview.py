from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0015_seed_cars'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=100)),
                ('vehicle_purchased', models.CharField(max_length=150)),
                ('rating', models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], default=5)),
                ('review_text', models.TextField()),
                ('date_submitted', models.DateTimeField(auto_now_add=True)),
                ('is_approved', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date_submitted'],
            },
        ),
    ]
