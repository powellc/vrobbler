# Generated by Django 4.2.13 on 2024-08-06 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0014_alter_userprofile_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="bgg_username",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
