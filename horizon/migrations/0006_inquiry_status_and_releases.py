from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0005_discount_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='inquiry',
            name='status',
            field=models.CharField(
                choices=[('new','New'),('processing','Processing'),('resolved','Resolved')],
                default='new', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='inquiry',
            name='admin_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='inquiry',
            name='car',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='inquiries',
                to='horizon.car',
            ),
        ),
    ]
