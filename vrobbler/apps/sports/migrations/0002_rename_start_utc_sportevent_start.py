# Generated by Django 4.1.5 on 2023-01-14 21:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sports', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sportevent',
            old_name='start_utc',
            new_name='start',
        ),
    ]
