# Generated by Django 4.1.5 on 2023-03-13 04:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sports", "0010_rename_run_time_sportevent_run_time_seconds"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sport",
            name="default_event_run_time",
        ),
    ]
