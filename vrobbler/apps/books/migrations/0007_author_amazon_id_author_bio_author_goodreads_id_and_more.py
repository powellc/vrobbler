# Generated by Django 4.1.5 on 2023-03-06 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0006_alter_page_duration_seconds_alter_page_start_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="author",
            name="amazon_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="bio",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="goodreads_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="isni",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="librarything_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="wikidata_id",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="author",
            name="wikipedia_url",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
