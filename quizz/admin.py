from django.contrib import admin
from .models import Subject, Lecture, Question, Test, Quizz, QuizzMode
# Register your models here.
admin.site.register(Subject)
admin.site.register(Lecture)
admin.site.register(Question)
admin.site.register(Test)
admin.site.register(Quizz)
admin.site.register(QuizzMode)