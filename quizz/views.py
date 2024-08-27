from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Subject, Lecture, Question, Test, Quizz, QuizzMode, UserSettings
from .forms import ImportExcelForm, SubjectFilterForm, LectureFilterForm, QuestionFilterForm, QuizzFilterForm, SubjectUpdateForm, LectureUpdateForm, QuestionUpdateForm, QuizzUpdateForm, CreateQuizzForm, UserSettingsForm
from .tasks import import_task
import random
from .utils import *
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext as _
import pandas as pd
from django.http import HttpResponse
from io import BytesIO

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
                Subject.objects.create(name=name, short_name = short_name, user=request.user)
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
    filterForm = LectureFilterForm(request.GET)
    subject = get_object_or_404(Subject, pk=id)
    lectures = Lecture.objects.filter(subject_id=id)
    updateForm = SubjectUpdateForm(instance=subject)
    addForm = LectureUpdateForm()

    questions = Question.objects.filter(lecture__in=lectures)
    tests = Test.objects.filter(question__in=questions)
    user_tests = tests.filter(user=user)
    chart = get_custom_scores(user_tests, request)

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
                Lecture.objects.create(name=name, subject=subject).save()
                message_added(request,name,'Le nouveau chapitre')
    info = {_('Subject'):subject,
             _('Amount of lectures'):lectures.count(),
            _('Amount of questions'):questions.count()}
    info, chart = get_info_chart(request,info,tests)
    lectures = paginate_children(request,lectures)
    fields = {'name':'Nom'}
    action = 'subject'
    context = prepare_render_context(action, filterForm, lectures, request, fields, object=subject, childurl='lecture', deleteurl='delete_subject', updateForm=updateForm, addForm=addForm,parenturl='subjects', chart=chart, info=info)
    context.update({'export':True})
    return update_page(request,chart,action,context)

def lecture(request,id):
    filterForm = QuestionFilterForm(request.GET)
    lecture = get_object_or_404(Lecture, pk=id)
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
                Question.objects.create(question=question, answer=answer, lecture=lecture).save()
                message_added(request,question,'La nouvelle question')

    if filterForm.is_valid():
        questions = filterForm.filter_queryset(questions)
    info={_('Subject'):lecture.subject,
        _('Lecture'):lecture,
        _('Amount of questions'):questions.count()}
    info, chart = get_info_chart(request,info,tests)
    questions = paginate_questions(request,questions)
    fields = {'question':'Question','answer':'Réponse'}
    action = 'lecture'
    context = prepare_render_context(action, filterForm, questions, request, fields, object=lecture, childurl='question', deleteurl='delete_lecture', updateForm=updateForm, addForm=addForm, sort_by='question', parenturl='subject', parent=lecture.subject, chart=chart, info=info)
    return update_page(request,chart,action,context)

def question(request,id):
    question = get_object_or_404(Question, pk=id)
    tests = Test.objects.filter(question_id=id)
    updateForm = QuestionUpdateForm(instance=question)
    if request.method == 'POST':
        if request.POST['action'] == 'update':
            updateForm = QuestionUpdateForm(request.POST, instance=question)
            if updateForm.is_valid():
                question.question = updateForm.cleaned_data['question']
                question.answer = updateForm.cleaned_data['answer']
                question.save()
                message_modification(request,question.question)
    info={_('Subject'):question.lecture.subject,
          _('Lecture'):question.lecture,
          _('Question'):question.question,
          _('Answer'):question.answer}
    info, chart = get_info_chart(request,info,tests)
    tests = paginate_tests(request,tests)
    fields = {'date':_('Date'),'correct':_('Success'),'hints':_('Hints')}
    action = 'question'
    context = prepare_render_context(action, children=tests, request=request, fields=fields, object=question, childurl='test', deleteurl='delete_question', updateForm=updateForm, sort_by='date', parenturl='lecture', parent=question.lecture, chart=chart,info=info)
    return update_page(request,chart,action,context)

def test(request,id):
    test = get_object_or_404(Test,pk=id)
    context = prepare_render_context('test', request=request, object=test, parenturl='question', parent=test.question, gameurl=None)
    return render(request, 'quizz/test.html', context)

def delete_subject(request, id):
    subject = get_object_or_404(Subject, id=id)
    delete_object(request,subject)
    return redirect('subjects')

def delete_lecture(request, id):
    lecture = get_object_or_404(Lecture, id=id)
    delete_object(request,lecture)
    return redirect('subject', id=lecture.subject.id)

def delete_question(request, id):
    question = get_object_or_404(Question, id=id)
    delete_object(request, question)
    return redirect('lecture', id=question.lecture.id)

def delete_test(request, id):
    test = get_object_or_404(Test, id=id)
    delete_object(request, test)
    return redirect('question', test.question.id)

def delete_quizz(request, id):
    quizz = get_object_or_404(Quizz, id=id)
    delete_object(request, quizz)
    return redirect('quizzes')

def delete_object(request, object):
    if request.method == 'POST':
        object.delete()
        messages.success(request, _('The element has been successfully removed'))
    return None

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
    
    # Vérifier s'il y a des questions restantes
    if quizz.questions.exists():
        if not quizz.current_question:
            quizz.current_question = random.choice(quizz.questions.all())
    else:
        quizz.delete()
        return render(request, 'quizz/game_end.html')

    if request.method == 'POST' and request.POST.get('action') == 'attempt':
        user_answer = simplify(request.POST.get('answer'))
        correct_answer = simplify(quizz.current_question.answer)
        is_correct = user_answer == correct_answer

        Test.objects.create(
            date=timezone.now(),
            correct=is_correct,
            question=quizz.current_question,
            hints=quizz.hints
        ).save()

        if is_correct:
            messages.success(request, f"{quizz.current_question.answer} " + _("is a good answer!"))
        else:
            messages.error(request, f"{user_answer} "+ _("is a wrong answer, it was") + f": {quizz.current_question.answer}")
            if quizz.mode.name == "Error-free":
                quizz.questions.clear()

        if quizz.mode.name != "Error-free" or is_correct:
            quizz.questions.remove(quizz.current_question)

        if quizz.questions.exists():
            quizz.current_question = random.choice(quizz.questions.all())
        else:
            quizz.delete()
            return render(request, 'quizz/game_end.html')

    quizz.save()
    
    return render(request,
        'quizz/game.html', {
        'quizz': quizz,
        'count': quizz.questions.count(),
        'question': quizz.current_question,
        'hint': hide(quizz.current_question.answer)
    })

def game_end(request):
    return render(request, 'quizz/game_end.html')

def game_start(request,quizz_type,id=0):
    title = 'error'
    if quizz_type == 'subjects' :
        title = _('Tout')
        total_size = Question.objects.all().count()
    elif quizz_type == 'subject' :
        selected_subject = get_object_or_404(Subject,pk=id)
        title = selected_subject.name
        total_size = Question.objects.filter(lecture__subject=selected_subject).count()
    elif quizz_type == 'lecture' :
        selected_lecture = get_object_or_404(Lecture,pk=id)
        title = selected_lecture.name
        total_size = Question.objects.filter(lecture=selected_lecture).count()
    elif quizz_type == 'question' :
        selected_question = get_object_or_404(Question,pk=id)
        title = selected_question.question
        total_size = 1
    
    if request.method == 'POST':
        form = CreateQuizzForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            quizz_name = cleaned_data['quizz_name']
            selected_mode = cleaned_data['mode']
            hints = cleaned_data['hints']
            max_questions = cleaned_data['max_questions']

            if quizz_type == 'subjects' :
                questions = Question.objects.all().order_by('?')[:max_questions]
            elif quizz_type == 'subject' :
                questions = Question.objects.filter(lecture__subject=selected_subject).order_by('?')[:max_questions]
            elif quizz_type == 'lecture' :
                questions = Question.objects.filter(lecture=selected_lecture).order_by('?')[:max_questions]
            elif quizz_type == 'question':
                questions = selected_question.order_by('?')[:max_questions]

            # Créer le quizz sans les questions
            quizz = Quizz.objects.create(name=quizz_name, mode=selected_mode, hints=hints, user=request.user)

            # Associer les questions au quizz
            quizz.questions.set(questions)

            quizz.save()
            messages.success(request, _("The quizz") + f" {quizz.name} " + _("has been successfully created"))
            if request.POST.get('action') == 'save_and_play':
                return redirect('game',id=quizz.id)

    initial_data = {'quizz_name': title,'max_questions':total_size,'mode':QuizzMode.objects.get(name=_("Normal"))}
    form = CreateQuizzForm(initial=initial_data)
    return render(request, 'quizz/game_start.html',{'form':form, 'quizz_type':quizz_type, 'object_id':id, 'title': title})

def quizzes(request):
    filterForm = QuizzFilterForm(request.GET)
    quizzes = Quizz.objects.all()
    if filterForm.is_valid():
        quizzes = filterForm.filter_queryset(quizzes)
    quizzes = paginate_queryset(quizzes.order_by(f"{'-' if request.GET.get('order', 'asc') == 'desc' else ''}{request.GET.get('sort_by', 'name')}"), request, getChildrenPerPage(request))
    fields = {'name':_('Name'),'mode':_('Mode')}
    context = prepare_render_context('quizzes', filterForm, quizzes, request, fields, childurl='quizz', gameurl=None, property=False)
    return render(request, 'quizz/quizzes.html', context)

def quizz(request,id):
    quizz = get_object_or_404(Quizz, pk=id)
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
    context = prepare_render_context(None, request=request, object=quizz, deleteurl='delete_quizz', updateForm=updateForm, parenturl='quizzes', gameurl='game', quizz=True)
    return render(request, 'quizz/quizz.html', context)

def register(request):
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

def settings(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

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