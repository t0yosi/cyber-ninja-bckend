# Generated by Django 5.0.6 on 2024-05-13 13:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_alter_curriculum_course"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lesson",
            name="curriculum",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lessons",
                to="api.curriculum",
            ),
        ),
    ]
