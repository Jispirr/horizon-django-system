from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0008_chat_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='ticket_number',
            field=models.CharField(blank=True, default='', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='chatsession',
            name='subject',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='chatsession',
            name='priority',
            field=models.CharField(
                choices=[('low','Low'),('normal','Normal'),('high','High')],
                default='normal', max_length=10
            ),
        ),
        migrations.AddField(
            model_name='chatsession',
            name='admin_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='chatsession',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='chatsession',
            name='status',
            field=models.CharField(
                choices=[('open','Open'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed')],
                default='open', max_length=15
            ),
        ),
    ]
