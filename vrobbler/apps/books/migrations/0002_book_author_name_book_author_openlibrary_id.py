# Generated by Django 4.1.5 on 2023-03-06 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="author_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="book",
            name="author_openlibrary_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
