# Generated by Django 4.0.3 on 2024-08-25 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quizz', '0020_test_hints'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionquizz',
            name='question',
        ),
        migrations.RemoveField(
            model_name='questionquizz',
            name='quizz_ptr',
        ),
        migrations.RemoveField(
            model_name='subjectquizz',
            name='quizz_ptr',
        ),
        migrations.RemoveField(
            model_name='subjectquizz',
            name='subject',
        ),
        migrations.DeleteModel(
            name='LectureQuizz',
        ),
        migrations.DeleteModel(
            name='QuestionQuizz',
        ),
        migrations.DeleteModel(
            name='SubjectQuizz',
        ),
    ]
