# Generated by Django 4.0.3 on 2024-08-17 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0018_alter_question_question'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizz',
            name='hints',
            field=models.BooleanField(default=True),
        ),
    ]
