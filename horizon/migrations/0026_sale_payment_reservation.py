from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0025_discounteventcar'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sale_number', models.CharField(blank=True, max_length=20, unique=True)),
                ('sale_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('final_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('bank', 'Bank Financing'), ('inhouse', 'In-house Financing'), ('gcash', 'GCash'), ('card', 'Credit / Debit Card')], default='cash', max_length=20)),
                ('status', models.CharField(choices=[('reserved', 'Reserved'), ('confirmed', 'Confirmed'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='reserved', max_length=20)),
                ('reservation_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('notes', models.TextField(blank=True)),
                ('sold_by', models.CharField(blank=True, help_text='Sales agent name', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales', to='horizon.customer')),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sale_records', to='horizon.car')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('payment_type', models.CharField(choices=[('reservation', 'Reservation Fee'), ('downpayment', 'Down Payment'), ('installment', 'Instalment'), ('full', 'Full Payment')], default='full', max_length=20)),
                ('method', models.CharField(choices=[('cash', 'Cash'), ('bank', 'Bank Financing'), ('inhouse', 'In-house Financing'), ('gcash', 'GCash'), ('card', 'Credit / Debit Card')], default='cash', max_length=20)),
                ('reference_no', models.CharField(blank=True, max_length=80)),
                ('notes', models.TextField(blank=True)),
                ('paid_at', models.DateTimeField(auto_now_add=True)),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='horizon.sale')),
            ],
            options={'ordering': ['-paid_at']},
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reservation_number', models.CharField(blank=True, max_length=20, unique=True)),
                ('fee_paid', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('active', 'Active'), ('converted', 'Converted to Sale'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='active', max_length=20)),
                ('expires_on', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='horizon.customer')),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='horizon.car')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
