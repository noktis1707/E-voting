# Generated by Django 5.1.7 on 2025-03-15 19:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meeting', '0006_remove_questiondetail_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questiondetail',
            name='question_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detail', to='meeting.agenda'),
        ),
    ]
