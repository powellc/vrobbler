# Generated by Django 4.1.7 on 2023-11-22 23:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0002_rawgeolocation"),
    ]

    operations = [
        migrations.AddField(
            model_name="rawgeolocation",
            name="timestamp",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
