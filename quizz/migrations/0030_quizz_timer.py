# Generated by Django 4.0.3 on 2024-08-28 07:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0029_timermode_remove_quizz_question_time_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizz',
            name='timer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='quizz.timermode'),
        ),
    ]
