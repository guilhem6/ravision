from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('subjects/', views.subjects, name='subjects'),
    path('import_excel/',views.import_excel, name='import_excel'),
    path('subject/<int:id>/', views.subject, name='subject'),
    path('lecture/<int:id>/', views.lecture, name='lecture'),
    path('question/<int:id>/', views.question, name='question'),
    path('test/<int:id>/', views.test, name='test'),
    path('delete_subject/<int:id>/', views.delete_subject, name='delete_subject'),
    path('delete_lecture/<int:id>/', views.delete_lecture, name='delete_lecture'),
    path('delete_question/<int:id>/', views.delete_question, name='delete_question'),
    path('delete_test/<int:id>/', views.delete_test, name='delete_test'),
    path('delete_quizz/<int:id>/', views.delete_quizz, name='delete_quizz'),
    path('game_start/<str:quizz_type>/<int:id>/', views.game_start, name='game_start'),
    path('game/<int:id>/', views.game, name='game'),
    path('game_end/', views.game_end, name='game_end'),
    path('quizzes/', views.quizzes, name='quizzes'),
    path('quizz/<int:id>/', views.quizz, name='quizz'),
]