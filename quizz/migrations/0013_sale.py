# Generated by Django 4.0.3 on 2024-03-27 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0012_quizz_current_question_alter_quizz_questions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.CharField(max_length=50)),
                ('price', models.FloatField()),
            ],
        ),
    ]
