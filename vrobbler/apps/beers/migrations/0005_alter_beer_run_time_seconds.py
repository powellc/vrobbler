# Generated by Django 4.2.16 on 2025-01-22 03:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "beers",
            "0004_beerproducer_name_beerproducer_uuid_beerstyle_name_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="beer",
            name="run_time_seconds",
            field=models.IntegerField(default=900),
        ),
    ]
