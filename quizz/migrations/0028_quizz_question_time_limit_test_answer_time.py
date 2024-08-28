# Generated by Django 4.0.3 on 2024-08-28 07:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0027_test_expected_answer_test_given_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizz',
            name='question_time_limit',
            field=models.FloatField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='test',
            name='answer_time',
            field=models.FloatField(default=None, null=True),
        ),
    ]
