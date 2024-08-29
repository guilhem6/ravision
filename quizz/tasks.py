from celery import shared_task
from celery_progress.backend import ProgressRecorder
from .models import Subject, Lecture, Question, User, Quizz
import pandas as pd
from io import BytesIO
from django.utils.translation import gettext as _
from django.utils import timezone
from datetime import timedelta
import time

@shared_task(bind=True)
def import_task(self,name,short_name, user_id,file_content):
    progress_recorder = ProgressRecorder(self)
    user = User.objects.get(id=user_id)
    # Vérifier si un sujet avec le short_name existe déjà
    try:
        subject = Subject.objects.get(short_name=short_name)
    except Subject.DoesNotExist:
        # Créer un nouveau sujet s'il n'existe pas encore
        subject = Subject.objects.create(name=name, short_name=short_name,user=user,creation_date=timezone.now())
    # Utilisation de pandas pour lire les feuilles du fichier Excel
    xls = pd.ExcelFile(BytesIO(file_content), engine='openpyxl')
    sheets = xls.sheet_names
    number_lectures = len(sheets)
    i=0
    for sheet_name in sheets:
        lecture, created = Lecture.objects.get_or_create(name=sheet_name, subject=subject)
        if created:
            lecture.creation_date = timezone.now()
        lecture.save()
        # Lire la feuille actuelle dans un DataFrame
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        
        for index, row in df.iterrows():
            try :
                question_exists = Question.objects.filter(
                    question = row[0],  # Première colonne pour la question
                    answer = row[1],    # Deuxième colonne pour la réponse
                    lecture = lecture
                ).exists()
                # Si la question n'existe pas encore, la créer
                if not question_exists:
                    Question.objects.create(
                        question=row[0],  # Première colonne pour la question
                        answer=row[1],    # Deuxième colonne pour la réponse
                        lecture=lecture,
                        creation_date = timezone.now()
                    ).save()
            except KeyError as e:
                print(f'KeyError: {e} in sheet {sheet_name} at row {index}')
                continue  # Skip this row
        i+=1
        progress_recorder.set_progress(i + 1, number_lectures)
    return _("The file has been successfully imported")
    
@shared_task(bind=True)
def handle_timer(self,quiz_id, duration):
    """
    Gère le timer pour un quiz et expire le quiz si le temps est écoulé.
    """
    try:
        quizz = Quizz.objects.get(pk=quiz_id)
        progress_recorder = ProgressRecorder(self)
        i=duration
        task_id = quizz.timer_task_id

        # Marquer le quiz comme ayant un timer actif
        
        while i>0 and task_id==quizz.timer_task_id:
            quizz = Quizz.objects.get(pk=quiz_id)
            #print(f"Secondes restantes : {i}\nId de la tâche : {task_id}\nId de la tâche selon le quizz : {quizz.timer_task_id}" )
            time.sleep(1)
            i=i-1
            progress_recorder.set_progress(i, duration)
        if i==0:
            self.update_state(state='FAILURE', meta={'message': _("Time is up!")})
            quizz.timeout = True
            quizz.save()
            print('Temps écoulé')
            raise Exception(_("Time is up!"))  # Lever une exception pour marquer l'échec
            
    except Quizz.DoesNotExist:
        self.update_state(state='FAILURE', meta={'message': _("Quiz does not exist.")})
        return _("Error: Quiz does not exist.")
    return _("Question suivante !!!")