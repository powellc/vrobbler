# Generated by Django 4.1.5 on 2023-02-20 00:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrobbles', '0021_scrobble_book'),
    ]

    operations = [
        migrations.AddField(
            model_name='scrobble',
            name='book_pages_read',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
