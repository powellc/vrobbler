# Generated by Django 4.1.5 on 2023-01-22 20:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sports', '0004_alter_league_options_alter_sport_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sportevent',
            name='season',
        ),
    ]
