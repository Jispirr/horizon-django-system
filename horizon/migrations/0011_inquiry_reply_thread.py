from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0010_remove_inquiry_chat'),
    ]

    operations = [
        migrations.AddField(
            model_name='inquiry',
            name='reply_token',
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.CreateModel(
            name='InquiryReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inquiry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='horizon.inquiry')),
                ('sender', models.CharField(choices=[('visitor', 'Visitor'), ('admin', 'Admin')], max_length=10)),
                ('body', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['sent_at']},
        ),
    ]
