from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0026_sale_payment_reservation'),
    ]

    operations = [
        # Remove old sales tables
        migrations.DeleteModel(name='Payment'),
        migrations.DeleteModel(name='Reservation'),
        migrations.DeleteModel(name='Sale'),

        # Add ActivityLog
        migrations.CreateModel(
            name='ActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('add',    'Added'),
                        ('edit',   'Edited'),
                        ('delete', 'Deleted'),
                        ('status', 'Status Changed'),
                        ('other',  'Other'),
                    ],
                    default='other', max_length=20,
                )),
                ('section',    models.CharField(max_length=60)),
                ('detail',     models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
