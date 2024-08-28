from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



# Create your models here.
class Subject(models.Model):
    private = models.BooleanField(default=False)
    name = models.CharField(max_length = 255,default="")
    short_name = models.CharField(max_length = 3,default="",unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    creation_date = models.DateField(null=True, default=None, blank=True)
    last_change_date = models.DateField(null=True, default=None, blank=True)


    def __str__(self):
        return self.name
    def as_dict(self):
        return {
            'name': self.name,
            'short_name': self.short_name
        }
    def form(self):
        return ['Nom','Trigramme']
    
    def save(self, *args, **kwargs):
        self.last_change_date = timezone.now()
        super().save(*args, **kwargs)

class Lecture(models.Model):
    name = models.CharField(max_length=255, default="")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    creation_date = models.DateField(null=True, default=None, blank=True)
    last_change_date = models.DateField(null=True, default=None, blank=True)

    def __str__(self):
        return self.name

    def as_dict(self):
        return {'name': self.name,}

    def save(self, *args, **kwargs):
        if self.user is None:
            self.user = self.subject.user
        self.last_change_date = timezone.now()
        self.subject.save()
        super().save(*args, **kwargs)

class Question(models.Model):
    answer = models.CharField(max_length=255, default="")
    question = models.CharField(max_length=511, default="")
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    creation_date = models.DateField(null=True, default=None, blank=True)
    last_change_date = models.DateField(null=True, default=None, blank=True)

    def __str__(self):
        return self.question

    def as_dict(self):
        return {
            'question': self.question,
            'answer': self.answer,
        }

    def save(self, *args, **kwargs):
        if self.user is None:
            self.user = self.lecture.subject.user
        self.last_change_date = timezone.now()
        self.lecture.save()
        super().save(*args, **kwargs)

class Test(models.Model):
    date = models.DateField(null=True, default=None, blank=True)
    correct = models.BooleanField(default=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, default=1)
    hints = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    expected_answer = models.CharField(max_length=255, default="")
    given_answer = models.CharField(max_length=255, default="")
    answer_time = models.FloatField(null=True, default=None)

    def __str__(self):
        if self.correct:
            return f'Correct : {self.question}'
        else:
            return f'Incorrect : {self.question}'

    def as_dict(self):
        correct = 'NON'
        hints = 'OUI'
        if self.correct:
            correct = 'OUI'
        if self.hints:
            hints = 'OUI'
        return {
            'date': self.date,
            'correct': correct,
            'hints': hints,
        }

    def save(self, *args, **kwargs):
        if self.user is None:
            self.user = self.question.lecture.subject.user
        super().save(*args, **kwargs)


class QuizzMode(models.Model):
    name = models.CharField(max_length = 255,default="")
    def __str__(self):
        return self.name

class TimerMode(models.Model):
    name = models.CharField(max_length = 255,default="")
    def __str__(self):
        return self.name

class Quizz(models.Model):
    name = models.CharField(max_length = 255,default="")
    questions = models.ManyToManyField(Question, related_name='quizz_questions')
    mode = models.ForeignKey(QuizzMode, on_delete=models.CASCADE, default=1)
    hints = models.BooleanField(default=True)
    current_question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, default=None, related_name='current_question')
    private = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    creation_date = models.DateField(null=True, default=None, blank=True)
    last_change_date = models.DateField(null=True, default=None, blank=True)
    timer = models.ForeignKey(TimerMode, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.name + str(self.id)
    def as_dict(self):
        return {
            'name': self.name,
            'mode': self.mode.name,
        }
    def save(self, *args, **kwargs):
        self.last_change_date = timezone.now()
        super().save(*args, **kwargs)

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=False)
    language = models.CharField(max_length=10, choices=[('en', 'English'), ('fr', 'Français')], default='en')

    def __str__(self):
        return f"Settings for {self.user.username}"