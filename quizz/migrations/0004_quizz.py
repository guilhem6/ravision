# Generated by Django 4.0.3 on 2024-03-21 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0003_subject_short_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quizz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=255)),
                ('questions', models.ManyToManyField(to='quizz.question')),
            ],
        ),
    ]
