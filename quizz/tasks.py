from celery import shared_task
from celery_progress.backend import ProgressRecorder
from .models import Subject, Lecture, Question, User
import pandas as pd
from io import BytesIO
from django.utils.translation import gettext as _


@shared_task(bind=True)
def import_task(self,name,short_name, user_id,file_content):
    progress_recorder = ProgressRecorder(self)
    user = User.objects.get(id=user_id)
    # Vérifier si un sujet avec le short_name existe déjà
    try:
        subject = Subject.objects.get(short_name=short_name)
    except Subject.DoesNotExist:
        # Créer un nouveau sujet s'il n'existe pas encore
        subject = Subject.objects.create(name=name, short_name=short_name,user=user)
    # Utilisation de pandas pour lire les feuilles du fichier Excel
    xls = pd.ExcelFile(BytesIO(file_content), engine='openpyxl')
    sheets = xls.sheet_names
    number_lectures = len(sheets)
    i=0
    for sheet_name in sheets:
        lecture, created = Lecture.objects.get_or_create(name=sheet_name, subject=subject)
        lecture.save()
        # Lire la feuille actuelle dans un DataFrame
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        
        for index, row in df.iterrows():
            #print(row)
            #print(row[0])
            # Vérifier si la question existe déjà
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
                        lecture=lecture
                    ).save()
            except KeyError as e:
                print(f'KeyError: {e} in sheet {sheet_name} at row {index}')
                continue  # Skip this row
        i+=1
        progress_recorder.set_progress(i + 1, number_lectures)
    return _("The file has been successfully imported")
    
