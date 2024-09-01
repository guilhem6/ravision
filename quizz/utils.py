import matplotlib.pyplot as plt
import base64
from io import BytesIO
from collections import defaultdict
from django.shortcuts import render
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.utils.translation import gettext as _
from matplotlib.ticker import MaxNLocator
from django.http import HttpResponseForbidden

def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph

def get_plot(x, y_correct_with_hint, y_correct_without_hint, y_incorrect_with_hint, y_incorrect_without_hint, dark_mode):
    plt.switch_backend('AGG')
    plt.figure(figsize=(12, 8))  # Augmenter la taille du graphique pour plus de lisibilité
    
    # Définir les couleurs en fonction du mode
    if dark_mode:
        plt.gcf().patch.set_facecolor('#1e1e1e')  # Couleur de fond du graphique pour le mode sombre
        plt.gca().set_facecolor('#1e1e1e')  # Couleur de fond des axes pour le mode sombre
        title_color = 'white'
        tick_color = 'white'
        bar_colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78']
    else:
        plt.gcf().patch.set_facecolor('white')  # Couleur de fond du graphique pour le mode clair
        plt.gca().set_facecolor('white')  # Couleur de fond des axes pour le mode clair
        title_color = 'black'
        tick_color = 'black'
        bar_colors = ['#007bff', '#66b3ff', '#ff5733', '#ff9a33']

    plt.title(_('score evolution'), fontsize=16, color=title_color, fontweight='bold')

    # Empiler les barres pour chaque catégorie avec des couleurs adaptées
    plt.bar(x, y_correct_without_hint, color=bar_colors[0], edgecolor='black', linewidth=0.8)
    plt.bar(x, y_correct_with_hint, bottom=y_correct_without_hint, color=bar_colors[1], edgecolor='black', linewidth=0.8)
    plt.bar(x, y_incorrect_without_hint, bottom=[sum(y) for y in zip(y_correct_with_hint, y_correct_without_hint)], color=bar_colors[2], edgecolor='black', linewidth=0.8)
    plt.bar(x, y_incorrect_with_hint, bottom=[sum(y) for y in zip(y_correct_with_hint, y_correct_without_hint, y_incorrect_without_hint)], color=bar_colors[3], edgecolor='black', linewidth=0.8)

    plt.xticks(rotation=45, fontsize=12, color=tick_color, ha='right')
    plt.yticks(fontsize=12, color=tick_color)
    plt.tick_params(axis='both', which='both', colors=tick_color)  # Couleur des ticks
    plt.gca().spines['top'].set_visible(False)  # Enlever les bordures supérieures
    plt.gca().spines['right'].set_visible(False)  # Enlever les bordures droites

    # Définir les ticks de l'axe y pour n'afficher que des valeurs entières
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.tight_layout()
    
    # Sauvegarder le graphique dans un buffer pour le retourner en tant que graphique
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    graph = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return graph


def get_scores(tests, percentage=False, 
               show_correct_without_hint=True, 
               show_correct_with_hint=True, 
               show_incorrect_without_hint=True, 
               show_incorrect_with_hint=True,
               dark_mode=False):
    
    # Obtenir les scores pour chaque catégorie par jour
    categories = ['correct_with_hint', 'correct_without_hint', 'incorrect_with_hint', 'incorrect_without_hint']
    show_flags = [show_correct_with_hint, show_correct_without_hint, show_incorrect_with_hint, show_incorrect_without_hint]

    active_categories = []
    inactive_categories = []
    for i in range(4):
        if show_flags[i] :
            active_categories.append(categories[i])
        else:
            inactive_categories.append(categories[i])
    # Initialiser le dictionnaire pour chaque jour avec les différentes catégories
    score_by_day = defaultdict(lambda: {
        'total': 0, 
        'correct_with_hint': 0, 
        'correct_without_hint': 0,
        'incorrect_with_hint': 0, 
        'incorrect_without_hint': 0
    })

    # Mettre à jour le score par jour
    for test in tests:
        date = test.date.strftime('%d/%m/%Y')
        category = ('correct' if test.correct else 'incorrect') + ('_with_hint' if test.hints else '_without_hint')
        if category in active_categories:
            score_by_day[date]['total'] += 1
            score_by_day[date][category] += 1

    # Trier les dates
    dates = sorted([datetime.strptime(date, '%d/%m/%Y') for date in score_by_day.keys()])
    dates = [date.strftime('%d/%m/%Y') for date in dates[-15:]]

    if not dates:
        return None
    

    scores = {category: [] for category in categories}

    for date in dates:
        total = score_by_day[date]['total']
        for category in categories:
            score = score_by_day[date][category]
            if percentage and total > 0:
                score = (score / total) * 100
            scores[category].append(score)

    #for category in inactive_categories:
    #    scores[category] = []    

    return get_plot(
        dates, 
        scores['correct_with_hint'], 
        scores['correct_without_hint'], 
        scores['incorrect_with_hint'], 
        scores['incorrect_without_hint'],
        dark_mode
    )

def get_custom_scores(tests, request):
    values = ['1', None]
    percentage = (request.GET.get('percentage') in values)
    show_correct_without_hint = (request.GET.get('show_correct_without_hint') in values)
    show_correct_with_hint = (request.GET.get('show_correct_with_hint') in values)
    show_incorrect_without_hint = (request.GET.get('show_incorrect_without_hint') in values)
    show_incorrect_with_hint = (request.GET.get('show_incorrect_with_hint') in values)
    with_ai_check = (request.GET.get('with_ai_check') in values)
    without_ai_check = (request.GET.get('without_ai_check') in values)
    without_timer = (request.GET.get('without_timer') in values)
    s30_timer = (request.GET.get('s30_timer') in values)
    s60_timer = (request.GET.get('s60_timer') in values)
    if not with_ai_check:
        tests = tests.exclude(aicheck=False)
    if not without_ai_check:
        tests = tests.exclude(aicheck=True)
    if not without_timer:
        tests = tests.exclude(timer__name='No timer')
    if not s30_timer:
        tests = tests.exclude(timer__name='30s')
    if not s60_timer:
        tests = tests.exclude(timer__name='60s')
    return get_scores(tests, percentage, show_correct_without_hint, show_correct_with_hint, show_incorrect_without_hint, show_incorrect_with_hint, request.dark_mode)


def getChildrenPerPage(request):
    return request.GET.get('children_per_page', DEFAULT_PER_PAGE)

DEFAULT_PER_PAGE = "50"

mots_conserves = {"about",
                  "across",
                  "along",
                  "also",
                  "among",
                  "an",
                  "and",
                  "are",
                  "around",
                  "as",
                  "at",
                  "be",
                  "because",
                  "between",
                  "but",
                  "by",
                  "can",
                  "due",
                  "from",
                  "has",
                  "have",
                  "if",
                  "in",
                  "into",
                  "is",
                  "it",
                  "its",
                  "may",
                  "not",
                  "of",
                  "off",
                  "on",
                  "onto",
                  "or",
                  "over",
                  "per",
                  "some",
                  "such",
                  "that",
                  "the",
                  "then",
                  "these",
                  "they",
                  "this",
                  "those",
                  "through",
                  "to",
                  "using",
                  "we",
                  "what",
                  "when",
                  "whether",
                  "which",
                  "while",
                  "with",
                  "within",
                  "without",
                  "whereas",
                  "whereby",
                  "for"
                  }

def hide(sentence):
    mots = sentence.split()

    resultat = []
    for mot in mots:
        mot_formate = mot
        if mot.lower() not in mots_conserves:
            mot_formate = ''.join(['_' if c.isalnum() else c for c in mot])
        resultat.append(mot_formate)

    return ' '.join(resultat)


def simplify(chaine):
    resultat = ''.join([caractere.lower() for caractere in chaine if caractere.isalnum()])
    return resultat

def fill_questions(workbook,sheet_name,max_score):
    sheet = workbook[sheet_name]
    max_row = sheet.max_row
    questions =[]
    if max_row >= 2 :
        for line_number in range(2, max_row + 1):
            score = sheet.cell(row=line_number, column=5).value
            if type(score) != float and type(score) != int :
                questions.append((line_number, sheet_name))
            elif score<=max_score :
                questions.append((line_number, sheet_name))
    return questions

def ajax_check(request):    
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def update_chart(request,chart):
    return render(request, 'quizz/object_content/graph.html', {'chart': chart})

def paginate_children(request,children):
    return paginate_queryset(children.order_by(f"{'-' if request.GET.get('order', 'asc') == 'desc' else ''}{request.GET.get('sort_by', 'name')}"), request, getChildrenPerPage(request))

def paginate_questions(request,children):
    return paginate_queryset(children.order_by(f"{'-' if request.GET.get('order', 'asc') == 'desc' else ''}{request.GET.get('sort_by', 'question')}"), request, getChildrenPerPage(request))

def paginate_tests(request,children):
    return paginate_queryset(children.order_by(f"{'-' if request.GET.get('order', 'asc') == 'desc' else ''}{request.GET.get('sort_by', 'date')}"), request, getChildrenPerPage(request))

def update_page(request,chart,action,context):
    if ajax_check(request):
        return update_chart(request,chart)
    return render(request, f'quizz/{action}.html', context)


# Fonction utilitaire pour la pagination
def paginate_queryset(queryset, request, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

# Constantes globales pour les valeurs par défaut
AVAILABLE_CHILDREN_PER_PAGE = ["1", "5", "10", "15", "20", "50"]

# Fonction utilitaire pour préparer le contexte de rendu
def prepare_render_context(action, filterForm=None, children=None, request=None, fields=None, object=None, childurl=None, deleteurl=None, updateForm = None, addForm = None, sort_by='name', parenturl=None, parent=None, chart=None, quizz=None, gameurl='game_start', property=True,info=None):
    return {
        'children': children,
        'object': object,
        'parent':parent,
        'urls':{'action': action,
                'child': childurl,
                'delete': deleteurl,
                'parent': parenturl,
                'game': gameurl},
        'chart':chart,
        'children_per_page': getChildrenPerPage(request),
        'sort_by': request.GET.get('sort_by', sort_by),
        'order': request.GET.get('order', 'asc'),
        'forms':{'filter':filterForm,
                 'update':updateForm,
                 'add':addForm},
        'amounts_of_children': AVAILABLE_CHILDREN_PER_PAGE,
        'fields': fields,   
        'defaultvis':['1',None],
        'quizz':quizz,
        'property':property,
        'info':info
    }

def message_modification(request, name):
    messages.success(request, f"Les modifications de {name} bien été prises en compte")

def message_added(request,name,typenew):
    messages.success(request, f"{typenew} {name} "+ _("has been added successfully"))

def all_test_count(tests,user_tests):
    return {_('Amount of attempts'):tests.count(),
            _('Amount of successful attempts'):tests.filter(correct=True).count(),
            _('My amount of attempts'):user_tests.count(),
            _('My amount of successful attempts'):user_tests.filter(correct=True).count()}

def get_info_chart(request,info,tests):
    user = request.user
    user_tests = tests.filter(user=user)
    chart = get_custom_scores(user_tests, request)
    info.update(all_test_count(tests,user_tests))
    return info, chart

def forbidden_request():
    return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à cette page.")

def delete_object(request, object):
    if request.method == 'POST':
        object.delete()
        messages.success(request, _('The element has been successfully removed'))
    return None

def parse_questions(generated_text):
    """
    Fonction pour analyser le texte généré par l'API OpenAI et extraire les questions et réponses.
    """
    questions = []
    for line in generated_text.split("\n"):
        if line.startswith("Q:"):
            question_text = line[2:].strip()
            questions.append({'question': question_text, 'answer': ''})
        elif line.startswith("A:") and questions:
            answer_text = line[2:].strip()
            questions[-1]['answer'] = answer_text
    return questions