# Generated by Django 3.2.16 on 2023-01-27 23:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_remove_mfamodel_last_used'),
    ]

    operations = [
        migrations.AddField(
            model_name='activationid',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default='1970-01-01 00:00:00+00:00'),
            preserve_default=False,
        ),
    ]
