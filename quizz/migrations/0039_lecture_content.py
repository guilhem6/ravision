# Generated by Django 4.0.3 on 2024-08-30 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0038_remove_quizz_private'),
    ]

    operations = [
        migrations.AddField(
            model_name='lecture',
            name='content',
            field=models.CharField(default='', max_length=4095),
        ),
    ]
