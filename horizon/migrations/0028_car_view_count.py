from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0027_activitylog_remove_sales'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='view_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
