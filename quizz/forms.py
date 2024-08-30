from django import forms
from urllib.parse import urlencode
from .models import Subject, Lecture, Question, Quizz, QuizzMode, UserSettings, TimerMode
from django.utils.translation import gettext as _

class ImportExcelForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=False)
    short_name = forms.CharField(label=_('Trigram'), required=False, max_length=3)
    file_path = forms.FileField(
        label=_('Select Excel file'),
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'data-browse': _('Choose file'),  # Personnaliser le bouton de sélection
            'aria-label': _('Select an Excel file'),  # Texte d'accessibilité pour les lecteurs d'écran
        })
    )

class ObjectFilterForm(forms.Form):
    def as_url(self):
        non_empty_data = {key: value for key, value in self.cleaned_data.items() if value}
        return urlencode(non_empty_data)
    
    def filter_queryset(self, queryset, **kwargs):
        filters = {}
        for field in self.fields:
            if self.cleaned_data.get(field):
                filters[f"{field}__icontains"] = self.cleaned_data.get(field)
        return queryset.filter(**filters, **kwargs)

class SubjectFilterForm(ObjectFilterForm):
    name = forms.CharField(label=_('Name'), required=False)
    short_name = forms.CharField(label=_('Trigram'), required=False)

class LectureFilterForm(ObjectFilterForm):
    name = forms.CharField(label=_('Name'), required=False)

class QuestionFilterForm(ObjectFilterForm):
    question = forms.CharField(label=_('Question'), required=False)
    answer = forms.CharField(label=_('Answer'), required=False)

class QuizzFilterForm(ObjectFilterForm):
    name = forms.CharField(label=_('Name'), required=False)

class SubjectUpdateForm(forms.ModelForm): 
    class Meta:
        model = Subject
        fields = ['name', 'short_name', 'private' ]
        labels = {
            'name': _('Name'),
            'short_name': _('Trigram'),
            'private':_('Private')
        }

class LectureUpdateForm(forms.ModelForm): 
    class Meta:
        model = Lecture
        fields = ['name' ]
        labels = {
            'name': _('Name'),
        }

class QuestionUpdateForm(forms.ModelForm): 
    class Meta:
        model = Question
        fields = ['question','answer' ]
        labels = {
            'question': _('Question'),
            'answer':_('Answer')
        }

class QuizzUpdateForm(forms.ModelForm): 
    class Meta:
        model = Quizz
        fields = ['name','mode','hints','timer']
        labels = {
            'name': _('Name'),
            'mode': _('Mode'),
            'hints' : _('With hints'),
            'timer' : _('Timer mode')
            }


class CreateQuizzForm(forms.Form):
    quizz_name = forms.CharField(label=_('Name'), required=False)
    max_questions = forms.IntegerField(min_value=1)
    mode = forms.ModelChoiceField(queryset=QuizzMode.objects.all(), label=_('Mode'))
    hints = forms.BooleanField(label = _('With hints'), initial=True, required=False)
    timer = forms.ModelChoiceField(queryset=TimerMode.objects.all(), label=_('Timer mode'))
 
class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['dark_mode', 'language']
        labels = {
            'dark_mode': _('Dark mode'),
            'language': _('Language')
        }

class QuestionGenerationForm(forms.Form):
    num_questions = forms.IntegerField(label="Nombre de questions", min_value=1, max_value=20, initial=5)
    difficulty = forms.ChoiceField(
        label=_("Difficulté"),
        choices=[('easy', 'Facile'), ('medium', 'Moyen'), ('hard', 'Difficile')],
        initial='medium'
    )
    size_answers = forms.IntegerField(label="Taille maximale des réponses", min_value=1, max_value=200, initial=20)
    prompt = forms.CharField(
        label=_("Thème"),
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 3})
    )