from django.db import models
#from django.contrib.auth.models import User

# Create your models here.
class Subject(models.Model):
    name = models.CharField(max_length = 255,default="")
    short_name = models.CharField(max_length = 3,default="",unique=True)
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    def as_dict(self):
        return {
            'name': self.name,
            'short_name': self.short_name
        }
    def form(self):
        return ['Nom','Trigramme']

class Lecture(models.Model):
    name = models.CharField(max_length = 255,default="")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, default=1)
    def __str__(self):
        return self.name
    def as_dict(self):
        return {
            'name': self.name,
        }
    
class Question(models.Model):
    answer = models.CharField(max_length = 255,default="")
    question = models.CharField(max_length = 511,default="")
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, default=1)
    def __str__(self):
        return self.question
    def as_dict(self):
        return {
            'question': self.question,
            'answer': self.answer,
        }

class Test(models.Model):
    date = models.DateField(null=True, default=None, blank=True)
    correct = models.BooleanField(default=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, default=1)
    hints = models.BooleanField(default=True)
    def __str__(self):
        if self.correct:
            return f'Correct : {self.question}'
        else :
            return f'Incorrect : {self.question}'
    def as_dict(self):
        correct = 'NON'
        hints = 'OUI'
        if self.correct:
            correct =  'OUI'            
        if self.hints:
            hints='OUI'
        return {
            'date': self.date,
            'correct': correct,
            'hints': hints,
        }

class QuizzMode(models.Model):
    name = models.CharField(max_length = 255,default="")
    def __str__(self):
        return self.name

class Quizz(models.Model):
    name = models.CharField(max_length = 255,default="")
    questions = models.ManyToManyField(Question, related_name='quizz_questions')
    mode = models.ForeignKey(QuizzMode, on_delete=models.CASCADE, default=1)
    hints = models.BooleanField(default=True)
    current_question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, default=None, related_name='current_question')
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return self.name + str(self.id)
    def as_dict(self):
        return {
            'name': self.name,
            'mode': self.mode.name,
        }