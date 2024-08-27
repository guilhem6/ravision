from django import forms
from urllib.parse import urlencode
from .models import Subject, Lecture, Question, Quizz, QuizzMode, UserSettings
from django.utils.translation import gettext as _

class ImportExcelForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=False)
    short_name = forms.CharField(label=_('Trigram'), required=False, max_length=3)
    file_path = forms.FileField(label=_('Select Excel file'))

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
        fields = ['name','mode','hints']
        labels = {
            'name': _('Name'),
            'mode': _('Mode'),
            'hints' : _('With hints')
        }

class CreateQuizzForm(forms.Form):
    quizz_name = forms.CharField(label=_('Name'), required=False)
    max_questions = forms.IntegerField(min_value=1)
    mode = forms.ModelChoiceField(queryset=QuizzMode.objects.all(), label=_('Mode'))
    hints = forms.BooleanField(label = _('With hints'), initial=True, required=False)

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['dark_mode', 'language']
        labels = {
            'dark_mode': _('Dark mode'),
            'language': _('Language')
        }