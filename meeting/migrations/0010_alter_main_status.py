# Generated by Django 5.1.7 on 2025-03-19 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meeting', '0009_alter_main_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='main',
            name='status',
            field=models.IntegerField(blank=True, choices=[('1', 'Ожидается'), ('2', 'Разрешена регистрация'), ('3', 'Разрешена голосование'), ('4', 'Голосование завершено'), ('5', 'Собрание завершилось')], default='1', null=True),
        ),
    ]
