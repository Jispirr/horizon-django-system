from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0023_testdriverequest_is_read'),
    ]

    operations = [
        migrations.AddField(
            model_name='dealershipsettings',
            name='footer_tagline',
            field=models.CharField(
                blank=True,
                default='Premium vehicles, exceptional service. Your trusted dealership in Metro Manila.',
                help_text='Short description shown under the brand name in the footer',
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name='dealershipsettings',
            name='footer_copyright',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Custom copyright line. Leave blank to auto-generate from dealership name.',
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name='dealershipsettings',
            name='footer_show_nav',
            field=models.BooleanField(default=True, help_text='Show the Navigate links column'),
        ),
        migrations.AddField(
            model_name='dealershipsettings',
            name='footer_show_services',
            field=models.BooleanField(default=True, help_text='Show the Services links column'),
        ),
        migrations.AddField(
            model_name='dealershipsettings',
            name='footer_show_contact',
            field=models.BooleanField(default=True, help_text='Show the Contact details column'),
        ),
        migrations.AddField(
            model_name='dealershipsettings',
            name='footer_show_socials',
            field=models.BooleanField(default=True, help_text='Show social media icon links'),
        ),
    ]
