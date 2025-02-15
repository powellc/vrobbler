# Generated by Django 4.1.5 on 2023-03-06 16:34

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0004_remove_book_author_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="author",
            name="uuid",
            field=models.UUIDField(
                blank=True, default=uuid.uuid4, editable=False, null=True
            ),
        ),
    ]
