# Generated by Django 5.1.6 on 2025-03-06 21:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bingo", "0003_usertask_approval_date_usertask_rejection_reason_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usertask",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="task_photos/"),
        ),
    ]
