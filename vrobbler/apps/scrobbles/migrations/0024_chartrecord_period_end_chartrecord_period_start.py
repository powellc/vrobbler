# Generated by Django 4.1.5 on 2023-03-03 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrobbles', '0023_alter_audioscrobblertsvimport_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chartrecord',
            name='period_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chartrecord',
            name='period_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
