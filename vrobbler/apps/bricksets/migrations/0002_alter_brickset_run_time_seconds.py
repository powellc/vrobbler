# Generated by Django 4.2.16 on 2025-01-22 03:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bricksets", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="brickset",
            name="run_time_seconds",
            field=models.IntegerField(default=900),
        ),
    ]
