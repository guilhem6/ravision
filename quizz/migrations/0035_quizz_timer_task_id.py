# Generated by Django 4.0.3 on 2024-08-29 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0034_alter_quizz_timer_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizz',
            name='timer_task_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
