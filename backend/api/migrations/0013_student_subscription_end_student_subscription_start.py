# Generated by Django 5.0.6 on 2024-05-18 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0012_lesson_duration"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="subscription_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="student",
            name="subscription_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
