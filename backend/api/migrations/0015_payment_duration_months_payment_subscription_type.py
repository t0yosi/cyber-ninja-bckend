# Generated by Django 5.0.6 on 2024-05-27 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_payment"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="duration_months",
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="payment",
            name="subscription_type",
            field=models.CharField(default="subscribe", max_length=50),
            preserve_default=False,
        ),
    ]
