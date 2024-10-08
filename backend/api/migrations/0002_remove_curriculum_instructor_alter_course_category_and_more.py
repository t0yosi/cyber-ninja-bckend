# Generated by Django 5.0.6 on 2024-05-13 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="curriculum",
            name="instructor",
        ),
        migrations.AlterField(
            model_name="course",
            name="category",
            field=models.CharField(
                choices=[("FREE", "Free"), ("PAID", "Paid")], max_length=4
            ),
        ),
        migrations.AlterField(
            model_name="student",
            name="courses_enlisted",
            field=models.ManyToManyField(blank=True, null=True, to="api.course"),
        ),
    ]
