# Generated by Django 5.0.6 on 2024-05-14 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_course_difficulty_course_duration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="instructor",
            name="courses_taught",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
