from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Subject, Lecture, Question, Test, Quizz, QuizzMode, UserSettings, TimerMode
from .forms import ImportExcelForm, SubjectFilterForm, LectureFilterForm, QuestionFilterForm, QuizzFilterForm, SubjectUpdateForm, LectureUpdateForm, QuestionUpdateForm, QuizzUpdateForm, CreateQuizzForm, UserSettingsForm, QuestionGenerationForm
from .tasks import import_task, handle_timer
import random
from .utils import *
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext as _
import pandas as pd
from django.http import HttpResponse
from io import BytesIO
from ravision.celery import app
from django.http import JsonResponse
from openai import OpenAI
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

client = OpenAI(
    # This is the default and can be omitted
    api_key='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')



# Create your views here.
def index(request):
    return render(request,'quizz/index.html')

# Utilisation de la fonction prepare_render_context dans vos vues
def catalogue(request):
    filterForm = SubjectFilterForm(request.GET)
    subjects = Subject.objects.filter(private=False)
    tests = Test.objects.filter(question__lecture__subject__in=subjects)
    
    if filterForm.is_valid():
        subjects = filterForm.filter_queryset(subjects)
    if request.user.is_authenticated:
        info = {_('Amount of subjects'):subjects.count(),
        _('Amount of lectures'):Lecture.objects.filter(subject__in=subjects).count(),
        _('Amount of questions'):Question.objects.filter(lecture__subject__in=subjects).count()}
        info, chart = get_info_chart(request,info,tests)
    else :
        info, chart = None, None

    subjects = paginate_children(request,subjects)
    fields = {'name':_('Name'),'short_name':_('Trigram')}
    action = 'catalogue'
    context = prepare_render_context(action, filterForm, subjects, request, fields, childurl='subject', chart=chart, gameurl=None, property=False, info=info)
    return update_page(request,chart,action,context) 

def subjects(request):
    user = request.user

    if user.is_anonymous:
        return redirect('login')
    
    filterForm = SubjectFilterForm(request.GET)
    subjects = Subject.objects.filter(user=user)
    addForm = SubjectUpdateForm()
    tests = Test.objects.filter(user=user)
    
    chart = get_custom_scores(tests, request)
    
    if filterForm.is_valid():
        subjects = filterForm.filter_queryset(subjects)
    if request.method == 'POST':
        if request.POST['action'] == 'add':
            addForm = SubjectUpdateForm(request.POST)
            if addForm.is_valid():
                name = addForm.cleaned_data['name']
                short_name = addForm.cleaned_data['short_name']
                Subject.objects.create(name=name, short_name = short_name, user=request.user, creation_date = timezone.now())
                message_added(request,name,'La nouvelle matière')
    info = {_('Amount of subjects'):subjects.count(),
            _('Amount of lectures'):Lecture.objects.filter(user=user).count(),
            _('Amount of questions'):Question.objects.filter(user=user).count()}
    info, chart = get_info_chart(request,info,tests)
    subjects = paginate_children(request,subjects)
    fields = {'name':_('Name'),'short_name':_('Trigram')}
    action = 'subjects'
    context = prepare_render_context(action, filterForm, subjects, request, fields, childurl='subject', addForm = addForm, chart=chart,property=False,info=info)
    return update_page(request,chart,action,context)
    
def subject(request, id):
    user = request.user

    if user.is_anonymous:
        return redirect('login')
    
    filterForm = LectureFilterForm(request.GET)
    subject = get_object_or_404(Subject, pk=id)

    # Vérifier les conditions d'accès
    if subject.private and user != subject.user:
        return forbidden_request()
    
    lectures = Lecture.objects.filter(subject_id=id)
    updateForm = SubjectUpdateForm(instance=subject)
    addForm = LectureUpdateForm()

    questions = Question.objects.filter(lecture__in=lectures)
    tests = Test.objects.filter(question__in=questions)

    if filterForm.is_valid():
        lectures = filterForm.filter_queryset(lectures)

    if request.method == 'POST':
        if request.POST['action'] == 'update':
            updateForm = SubjectUpdateForm(request.POST, instance=subject)
            if updateForm.is_valid():
                subject.name = updateForm.cleaned_data['name']
                subject.short_name = updateForm.cleaned_data['short_name']
                subject.save()
                message_modification(request,subject.name)
        elif request.POST['action'] == 'add':
            addForm = LectureUpdateForm(request.POST)
            if addForm.is_valid():
                name = addForm.cleaned_data['name']
                Lecture.objects.create(name=name, subject=subject,creation_date = timezone.now()).save()
                message_added(request,name,'Le nouveau chapitre')
    info = {_('User'):user,
            _('Subject'):subject,
            _('Amount of lectures'):lectures.count(),
            _('Amount of questions'):questions.count(),
            _('Creation date'):subject.creation_date,
            _('Last update'):subject.last_change_date}
    info, chart = get_info_chart(request,info,tests)
    lectures = paginate_children(request,lectures)
    fields = {'name':'Nom'}
    action = 'subject'
    context = prepare_render_context(action, filterForm, lectures, request, fields, object=subject, childurl='lecture', deleteurl='delete_subject', updateForm=updateForm, addForm=addForm,parenturl='subjects', chart=chart, info=info)
    context.update({'export':True})
    return update_page(request,chart,action,context)

def lecture(request,id):
    user = request.user
    filterForm = QuestionFilterForm(request.GET)
    lecture = get_object_or_404(Lecture, pk=id)

    if user.is_anonymous:
        return redirect('login')

    # Vérifier les conditions d'accès
    subject = lecture.subject
    if subject.private and user != subject.user:
        return forbidden_request()
    
    questions = Question.objects.filter(lecture_id=id)
    updateForm = LectureUpdateForm(instance=lecture)
    addForm = QuestionUpdateForm()

    tests = Test.objects.filter(question__in=questions)

    if request.method == 'POST':
        if request.POST['action'] == 'update':
            updateForm = LectureUpdateForm(request.POST, instance=lecture)
            if updateForm.is_valid():
                lecture.name = updateForm.cleaned_data['name']
                lecture.save()
                message_modification(request,lecture.name)
        elif request.POST['action'] == 'add':
            addForm = QuestionUpdateForm(request.POST)
            if addForm.is_valid():
                question = addForm.cleaned_data['question']
                answer = addForm.cleaned_data['answer']
                Question.objects.create(question=question, answer=answer, lecture=lecture, creation_date = timezone.now()).save()
                message_added(request,question,'La nouvelle question')

    if filterForm.is_valid():
        questions = filterForm.filter_queryset(questions)
    info={_('User'):user,
          _('Subject'):lecture.subject,
          _('Lecture'):lecture,
          _('Amount of questions'):questions.count(),
          _('Creation date'):lecture.creation_date,
          _('Last update'):lecture.last_change_date}
    info, chart = get_info_chart(request,info,tests)
    questions = paginate_questions(request,questions)
    fields = {'question':'Question','answer':'Réponse'}
    action = 'lecture'
    context = prepare_render_context(action, filterForm, questions, request, fields, object=lecture, childurl='question', deleteurl='delete_lecture', updateForm=updateForm, addForm=addForm, sort_by='question', parenturl='subject', parent=lecture.subject, chart=chart, info=info)
    context.update({'generate':True})
    return update_page(request,chart,action,context)

def question(request,id):
    user = request.user
    question = get_object_or_404(Question, pk=id)
    tests = Test.objects.filter(question_id=id)

    if user.is_anonymous:
        return redirect('login')

    # Vérifier les conditions d'accès
    subject = question.lecture.subject
    if subject.private and user != subject.user:
        return forbidden_request()
    
    updateForm = QuestionUpdateForm(instance=question)
    if request.method == 'POST':
        if request.POST['action'] == 'update':
            updateForm = QuestionUpdateForm(request.POST, instance=question)
            if updateForm.is_valid():
                question.question = updateForm.cleaned_data['question']
                question.answer = updateForm.cleaned_data['answer']
                question.save()
                message_modification(request,question.question)
    info={_('User'):user,
          _('Subject'):question.lecture.subject,
          _('Lecture'):question.lecture,
          _('Question'):question.question,
          _('Answer'):question.answer,
          _('Creation date'):question.creation_date,
          _('Last update'):question.last_change_date}
    info, chart = get_info_chart(request,info,tests)
    tests = paginate_tests(request,tests)
    fields = {'date':_('Date'),'correct':_('Success'),'hints':_('Hints'),'aicheck':_('AI check'),'timer':_('Timer')}
    action = 'question'
    context = prepare_render_context(action, children=tests, request=request, fields=fields, object=question, childurl='test', deleteurl='delete_question', updateForm=updateForm, sort_by='date', parenturl='lecture', parent=question.lecture, chart=chart,info=info)
    return update_page(request,chart,action,context)

def test(request,id):
    test = get_object_or_404(Test,pk=id)

    # Vérifier les conditions d'accès
    subject = test.question.lecture.subject
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if subject.private and user != subject.user:
        return forbidden_request()
    

    info = {_('User'):user,
          _('Subject'):test.question.lecture.subject,
          _('Lecture'):test.question.lecture,
          _('Question'):test.question.question,
          _('Correct'):test.correct,
          _('Expected answer'):test.expected_answer,
          _('Given answer'):test.given_answer,
          _('Hints'):test.hints,
          _('Timer'):test.timer.name,
          _('AI check'):test.aicheck,
          _('Date'):test.date
          }
    context = prepare_render_context('test', request=request, object=test, parenturl='question', parent=test.question, gameurl=None, info=info)

    return render(request, 'quizz/test.html', context)

def delete_subject(request, id):
    subject = get_object_or_404(Subject, id=id)

    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if subject.private and user != subject.user:
        return forbidden_request()
    
    delete_object(request,subject)
    return redirect('subjects')

def delete_lecture(request, id):
    lecture = get_object_or_404(Lecture, id=id)

    subject = lecture.subject
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if subject.private and user != subject.user:
        return forbidden_request()
    
    delete_object(request,lecture)
    return redirect('subject', id=lecture.subject.id)

def delete_question(request, id):
    question = get_object_or_404(Question, id=id)

    subject = question.lecture.subject
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if subject.private and user != subject.user:
        return forbidden_request()
    
    delete_object(request, question)
    return redirect('lecture', id=question.lecture.id)

def delete_test(request, id):
    test = get_object_or_404(Test, id=id)

    subject = test.question.lecture.subject
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if subject.private and user != subject.user:
        return forbidden_request()
    
    delete_object(request, test)
    return redirect('question', test.question.id)

def delete_quizz(request, id):
    quizz = get_object_or_404(Quizz, id=id)

    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if user != quizz.user:
        return forbidden_request()
    
    delete_object(request, quizz)
    return redirect('quizzes')

def import_excel(request):
    task_id = None
    if request.method == 'POST':
        form = ImportExcelForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file_path']
            name = request.POST.get('name')
            short_name = request.POST.get('short_name')
            file_content = excel_file.read()
            result = import_task.delay(name,short_name,request.user.id,file_content)
            task_id = result.task_id
            request.session['task_id'] = task_id
    else:
        form = ImportExcelForm()
    return render(request,'quizz/import_excel.html', {'form': form, 'task_id': task_id})

def game(request, id):
    quizz = get_object_or_404(Quizz, pk=id)
    
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if user != quizz.user:
        return forbidden_request()

    # Vérifier s'il y a des questions restantes
    if quizz.questions.exists():
        if not quizz.current_question:
            quizz.current_question = random.choice(quizz.questions.all())
    else:
        quizz.delete()
        return render(request, 'quizz/game_end.html')
    
    #Si on clique sur soumettre
    if request.method == 'POST' and request.POST.get('action') == 'attempt':
        user_answer = simplify(request.POST.get('answer'))
        correct_answer = simplify(quizz.current_question.answer)
        is_correct = False
        print('hello')

        #si le temps n'a été écoulé
        if not quizz.timeout or quizz.timer.name=="No timer":
            print('hello2 ')
            is_correct = user_answer == correct_answer
            if not is_correct and quizz.aicheck:
                print('hello3 ')
                openai_prompt = f"The question is: '{quizz.current_question.question}.\nThe given answer is '{quizz.current_question.answer}'.\nIs the following question also valid ?\n{request.POST.get('answer')}\n\nAnswer yes or no"
                chat_completion = client.chat.completions.create(
                messages=[{"role": "user","content": openai_prompt,}],
                model="gpt-3.5-turbo",
            )

            # Traitement de la réponse de l'API pour obtenir les questions
                generated_text = chat_completion.choices[0].message.content
                print(generated_text)
                if simplify(generated_text[0]) == 'y':
                    is_correct = True
        #Réinitialiser l'ID de la tâche
        quizz.save()

        Test.objects.create(
            date=timezone.now(),
            correct=is_correct,
            question=quizz.current_question,
            hints=quizz.hints,
            expected_answer = quizz.current_question.answer,
            given_answer = request.POST.get('answer'),
            aicheck = quizz.aicheck,
            timer = quizz.timer
        ).save()

        if quizz.timeout:
            messages.error(request, f"Too late! It was" + f": {quizz.current_question.answer}")
        elif is_correct:
            messages.success(request, f"{quizz.current_question.answer} " + _("is a good answer!"))
        else:
            messages.error(request, f"{user_answer} "+ _("is a wrong answer, it was") + f": {quizz.current_question.answer}")
            if quizz.mode.name == "Error-free":
                quizz.questions.clear()

        quizz.timer_task_id = None 
        quizz.timeout=False
        quizz.save()

        if quizz.mode.name != "Error-free" or is_correct:
            quizz.questions.remove(quizz.current_question)

        if quizz.questions.exists():
            quizz.current_question = random.choice(quizz.questions.all())
        else:
            quizz.delete()
            return render(request, 'quizz/game_end.html')
    
    #S'il n'y a pas de timer, lancer un timer
    if quizz.timer.name in ['30s', '60s'] and not quizz.timer_task_id:
        duration = 30 if quizz.timer.name == '30s' else 60
                # Lancer la tâche et enregistrer l'ID de la tâche
        task = handle_timer.apply_async((quizz.id, duration))
        quizz.timer_task_id = task.id  # Stocker l'ID de la tâche
        quizz.save()
        #result = handle_timer.delay(quizz.id, duration)
        #task_id = quizz.timer_task_id
        request.session['task_id'] = quizz.timer_task_id

    quizz.save()

    return render(request, 'quizz/game.html', {
        'quizz': quizz,
        'count': quizz.questions.count(),
        'question': quizz.current_question,
        'hint': hide(quizz.current_question.answer),
        'task_id':quizz.timer_task_id
    })

def check_quizz_timeout(request, quiz_id):
    try:
        quizz = Quizz.objects.get(pk=quiz_id)
        response_data = {
            'timeout': quizz.timeout  # Récupère l'état actuel du timeout
        }
    except Quizz.DoesNotExist:
        response_data = {
            'timeout': False
        }
    return JsonResponse(response_data)

def game_end(request):
    return render(request, 'quizz/game_end.html')

def game_start(request,quizz_type,id=0):
    title = 'error'
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if quizz_type == 'subjects' :
        title = _('Tout')
        total_size = Question.objects.filter(lecture__subject__user=user).count()
    elif quizz_type == 'subject' :
        selected_subject = get_object_or_404(Subject,pk=id)
        if user != selected_subject.user:
            return forbidden_request()
        title = selected_subject.name
        total_size = Question.objects.filter(lecture__subject=selected_subject,lecture__subject__user=user).count()
    elif quizz_type == 'lecture' :
        selected_lecture = get_object_or_404(Lecture,pk=id)
        if user != selected_lecture.subject.user:
            return forbidden_request()
        title = selected_lecture.name
        total_size = Question.objects.filter(lecture=selected_lecture,lecture__subject__user=user).count()
    elif quizz_type == 'question' :
        selected_question = get_object_or_404(Question,pk=id)
        if user != selected_question.lecture.subject.user:
            return forbidden_request()
        title = selected_question.question
        total_size = 1
    else :
        return forbidden_request()
    if request.method == 'POST':
        form = CreateQuizzForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            quizz_name = cleaned_data['quizz_name']
            selected_mode = cleaned_data['mode']
            hints = cleaned_data['hints']
            max_questions = cleaned_data['max_questions']
            selected_timer = cleaned_data['timer']
            aicheck=cleaned_data['aicheck']

            if quizz_type == 'subjects' :
                questions = Question.objects.all().order_by('?')[:max_questions]
            elif quizz_type == 'subject' :
                questions = Question.objects.filter(lecture__subject=selected_subject).order_by('?')[:max_questions]
            elif quizz_type == 'lecture' :
                questions = Question.objects.filter(lecture=selected_lecture).order_by('?')[:max_questions]
            elif quizz_type == 'question':
                questions = Question.objects.filter(id=selected_question.id)

            # Créer le quizz sans les questions
            quizz = Quizz.objects.create(name=quizz_name, mode=selected_mode, hints=hints, user=request.user, creation_date = timezone.now(), timer=selected_timer,aicheck=aicheck)

            # Associer les questions au quizz
            quizz.questions.set(questions)

            quizz.save()
            messages.success(request, _("The quizz") + f" {quizz.name} " + _("has been successfully created"))
            if request.POST.get('action') == 'save_and_play':
                return redirect('game',id=quizz.id)

    initial_data = {'quizz_name': title,'max_questions':total_size,'mode':QuizzMode.objects.get(name="Normal"),'timer':TimerMode.objects.get(name="No timer")}
    form = CreateQuizzForm(initial=initial_data)
    return render(request, 'quizz/game_start.html',{'form':form, 'quizz_type':quizz_type, 'object_id':id, 'title': title})

def quizzes(request):
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    filterForm = QuizzFilterForm(request.GET)
    quizzes = Quizz.objects.filter(user=user)
    if filterForm.is_valid():
        quizzes = filterForm.filter_queryset(quizzes)
    quizzes = paginate_queryset(quizzes.order_by(f"{'-' if request.GET.get('order', 'asc') == 'desc' else ''}{request.GET.get('sort_by', 'name')}"), request, getChildrenPerPage(request))
    fields = {'name':_('Name'),'mode':_('Mode')}
    context = prepare_render_context('quizzes', filterForm, quizzes, request, fields, childurl='quizz', gameurl=None, property=False)
    return render(request, 'quizz/quizzes.html', context)

def quizz(request,id):
    quizz = get_object_or_404(Quizz, pk=id)
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if user != quizz.user:
        return forbidden_request()
    updateForm = QuizzUpdateForm(instance=quizz)
    if request.method == 'POST':
        if request.POST['action'] == 'update':
            updateForm = QuizzUpdateForm(request.POST, instance=quizz)
            if updateForm.is_valid():
                cleaned_data = updateForm.cleaned_data
                quizz.name = cleaned_data['name']
                quizz.mode = cleaned_data['mode']
                quizz.save()
                message_modification(request,quizz.name)
    info = {_('Name'):quizz.name,
            _('Remaining questions'):quizz.questions.count(),
            _('Mode'):quizz.mode.name,
            _('Timer mode'):quizz.timer.name,
            _('Hints'):quizz.hints,
            _('AI check'):quizz.aicheck,
            _('Creation date'):quizz.creation_date,
            _('Last update'):quizz.last_change_date
            }
    context = prepare_render_context(None, request=request, object=quizz, deleteurl='delete_quizz', updateForm=updateForm, parenturl='quizzes', gameurl='game', quizz=True, info=info)
    return render(request, 'quizz/quizz.html', context)

def register(request):
    if not request.user.is_anonymous:
        logout(request)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _("Welcome")+ f", {user.username}")
            return redirect('subjects')  # Redirige vers le tableau de bord après inscription
    else:
        form = UserCreationForm()
    return render(request, 'quizz/register.html', {'form': form})

def user_login(request):
    if not request.user.is_anonymous:
        logout(request)
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('subjects')  # Redirige vers le tableau de bord après connexion
    else:
        form = AuthenticationForm()
    return render(request, 'quizz/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')  # Redirige vers la page de connexion après déconnexion

def user_account(request):
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'logout':
            logout(request)
            messages.success(request, _("You have been logged out."))
            return redirect('login')  # Redirige vers la page de connexion après déconnexion
        
        elif action == 'delete':
            user.delete()  # Supprime le compte utilisateur
            messages.success(request, _("Your account has been successfully removed."))
            return redirect('register')  # Redirige vers la page d'inscription après suppression du compte
    
    context={'info':{_('Login'):user.username,
                     _('Amount of subjects'):Subject.objects.filter(user=user).count(),
                     _('Amount of lectures'):Lecture.objects.filter(user=user).count(),
                     _('Amount of questions'):Question.objects.filter(user=user).count(),
                     _('Amount of attempts'):Test.objects.filter(user=user).count(),
                     _('Amount of successful attempts'):Test.objects.filter(user=user, correct=True).count()}}
    return render(request, 'quizz/account.html',context)

def download_excel(request, id):
    # Récupérer le sujet correspondant
    subject = Subject.objects.get(id=id)
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if user != subject.user:
        return forbidden_request()
    # Créer un objet Excel
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Ajouter une feuille pour chaque lecture
    lectures = Lecture.objects.filter(subject=subject)
    for lecture in lectures:
        # Récupérer les questions et réponses associées
        questions = Question.objects.filter(lecture=lecture)
        
        # Créer un DataFrame pour chaque lecture
        data = {
            'Question': [q.question for q in questions],
            'Answer': [q.answer for q in questions]
        }
        df = pd.DataFrame(data)
        
        # Écrire le DataFrame dans une feuille Excel
        df.to_excel(writer, sheet_name=lecture.name, index=False, header=False)

    # Finaliser l'écriture du fichier Excel
    writer.save()
    output.seek(0)

    # Configurer la réponse HTTP pour le téléchargement
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={subject.short_name}.xlsx'

    return response

def generate_questions(request, lecture_id):
    lecture = get_object_or_404(Lecture, pk=lecture_id)
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if user != lecture.subject.user:
        return forbidden_request()
    default_prompt = f"{lecture.subject.name} - {lecture.name}."
    form = QuestionGenerationForm(initial={'prompt': default_prompt})
    return render(request, 'quizz/generate_questions.html', {'form': form, 'lecture': lecture})

    
@login_required
@csrf_exempt
def generate(request,lecture_id):
    lect = get_object_or_404(Lecture, pk=lecture_id)
    user = request.user
    if user.is_anonymous:
        return redirect('login')
    if user != lect.subject.user:
        return forbidden_request()
    if request.method == 'POST':
        form = QuestionGenerationForm(request.POST)
        if form.is_valid():
            num_questions = form.cleaned_data['num_questions']
            difficulty = form.cleaned_data['difficulty']
            prompt = form.cleaned_data['prompt']
            size_answers = form.cleaned_data['size_answers']
            using_content = form.cleaned_data['using_content']
            # Appel à l'API OpenAI pour générer des questions
            openai_prompt = _("Générer") + f" {num_questions} " + _("questions-réponses ")
            if prompt!="" :
                openai_prompt += _("sur le thème de") + f" {prompt}, "
            openai_prompt += _("avec des réponses de maximum") + f" {size_answers} " + _("caractères.") + "\n" + _("Niveau de difficulté") + f" : {difficulty}\n" + _("Sous la forme suivante :") + "\nQ: ...\nA: ..."
            if using_content:
                openai_prompt += f"\n\nUtilise le texte suivant pour les questions :\n{lect.content}"
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user","content": openai_prompt,}],
                model="gpt-3.5-turbo",
            )

            # Traitement de la réponse de l'API pour obtenir les questions
            generated_text = chat_completion.choices[0].message.content
            #print(generated_text)
            questions_and_answers = parse_questions(generated_text)
            #print(questions_and_answers)

            return render(request, 'quizz/generated_questions.html', {
                'form': form,
                'questions': questions_and_answers,
                'lecture': lecture
            })
    return render(request, 'quizz/error.html')

def generate_content(request,lecture_id):
    try:
        lect = get_object_or_404(Lecture, pk=lecture_id)
        user = request.user
        if user.is_anonymous:
            return redirect('login')
        if user != lect.subject.user:
            return forbidden_request()
        openai_prompt = _("Génère un cours de 1000 caractères maximum sur ") + f"{lect.subject.name} : {lect.name}"
        chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": openai_prompt,
                        }
                    ],
                    model="gpt-3.5-turbo",
                )

        # Traitement de la réponse de l'API pour obtenir les questions
        generated_text = chat_completion.choices[0].message.content
        print(generated_text)
        lect.content = generated_text
        lect.save()
        # Renvoie de la réponse sous forme de JSON
        return JsonResponse({'status': 'success', 'content': generated_text})

    except Exception as e:
        # En cas d'erreur, renvoie une réponse d'erreur
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@csrf_exempt
def add_question(request):
    user = request.user
    if user.is_anonymous:
            return redirect('login')
    if request.method == 'POST':
        question_text = request.POST.get('question')
        answer_text = request.POST.get('answer')
        lecture_id = request.POST.get('lecture_id')

        try:
            lecture = Lecture.objects.get(id=lecture_id)
            if user != lecture.subject.user:
                return forbidden_request()
            question = Question.objects.create(
                question=question_text,
                answer=answer_text,
                lecture=lecture,
                user=request.user,
                creation_date = timezone.now()
            ).save()
            return JsonResponse({'status': 'success', 'message': 'Question added', 'question_id': question.id})
        except Lecture.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Lecture not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
@csrf_exempt
def add_all_questions(request):
    user = request.user
    if user.is_anonymous:
            return redirect('login')
    if request.method == 'POST':
        questions = request.POST.getlist('questions[]')
        lecture_id = request.POST.get('lecture_id')
        print(questions)

        try:
            lecture = Lecture.objects.get(id=lecture_id)
            if user != lecture.subject.user:
                return forbidden_request()
            for question_data in questions:
                question_text, answer_text = question_data.split('||')
                Question.objects.create(
                    question=question_text,
                    answer=answer_text,
                    lecture=lecture,
                    user=request.user,
                     creation_date = timezone.now()
                ).save()

            return JsonResponse({'status': 'success', 'message': 'All questions added'})
        except Lecture.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Lecture not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



def settings(request):
    user = request.user
    if user.is_anonymous:
            return redirect('login')
    user_settings, created = UserSettings.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            return redirect('settings')
    else:
        form = UserSettingsForm(instance=user_settings)

    context = {
        'form': form
    }
    return render(request, 'quizz/settings.html', context)