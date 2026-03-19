from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0006_inquiry_status_and_releases'),
    ]

    operations = [
        # Add chat_token to Inquiry
        migrations.AddField(
            model_name='inquiry',
            name='chat_token',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),

        # Create InquiryMessage table
        migrations.CreateModel(
            name='InquiryMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inquiry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='horizon.inquiry')),
                ('sender', models.CharField(choices=[('customer', 'Customer'), ('admin', 'Admin')], max_length=10)),
                ('body', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('is_seen', models.BooleanField(default=False)),
            ],
            options={'ordering': ['sent_at']},
        ),
    ]
