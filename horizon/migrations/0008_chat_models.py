from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0007_inquiry_chat'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',       models.CharField(max_length=100)),
                ('email',      models.EmailField()),
                ('token',      models.CharField(max_length=64, unique=True)),
                ('status',     models.CharField(choices=[('open','Open'),('closed','Closed')], default='open', max_length=10)),
                ('is_read',    models.BooleanField(default=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-started_at']},
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id',      models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='horizon.chatsession')),
                ('sender',  models.CharField(choices=[('visitor','Visitor'),('admin','Admin')], max_length=10)),
                ('body',    models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('is_seen', models.BooleanField(default=False)),
            ],
            options={'ordering': ['sent_at']},
        ),
    ]
