# Generated by Django 4.1.5 on 2023-01-22 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sports', '0006_alter_sportevent_event_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='sport',
            name='default_event_type',
            field=models.CharField(
                choices=[('UK', 'Unknown'), ('GA', 'Game'), ('MA', 'Match')],
                default='UK',
                max_length=2,
            ),
        ),
    ]
