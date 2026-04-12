from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0020_dealershipsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='dealershipsettings',
            name='brand_name',
            field=models.CharField(
                default='HORIZON', max_length=40,
                help_text='Short name shown in the navbar (e.g. HORIZON)'
            ),
        ),
        migrations.AddField(
            model_name='dealershipsettings',
            name='chat_avatar_letter',
            field=models.CharField(
                default='H', max_length=2,
                help_text='1-2 letter initial shown in the chat widget avatar'
            ),
        ),
    ]
