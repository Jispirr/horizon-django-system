from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('horizon', '0009_chatsession_ticket'),
    ]

    operations = [
        migrations.DeleteModel(name='InquiryMessage'),
        migrations.RemoveField(model_name='inquiry', name='chat_token'),
    ]
