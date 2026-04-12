from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0022_testdriverequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='testdriverequest',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
