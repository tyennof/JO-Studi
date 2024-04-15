# Generated by Django 5.0.3 on 2024-04-03 09:43

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('event_mgmt', '0009_alter_event_eventslug'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Eticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='qr_code')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='event_mgmt.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
