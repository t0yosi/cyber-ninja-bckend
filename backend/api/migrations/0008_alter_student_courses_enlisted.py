# Generated by Django 5.0.6 on 2024-05-14 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_course_image1_course_image2_course_image3"),
    ]

    operations = [
        migrations.AlterField(
            model_name="student",
            name="courses_enlisted",
            field=models.ManyToManyField(null=True, to="api.course"),
        ),
    ]
