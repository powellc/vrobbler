# Generated by Django 4.1.7 on 2023-08-26 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0016_book_locg_slug_book_summary"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="authors",
            field=models.ManyToManyField(
                blank=True, null=True, to="books.author"
            ),
        ),
    ]
