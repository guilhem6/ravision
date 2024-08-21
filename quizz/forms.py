from django import forms
from urllib.parse import urlencode
from .models import Subject, Lecture, Question, Quizz, QuizzMode

class ImportExcelForm(forms.Form):
    name = forms.CharField(label='Nom', required=False)
    short_name = forms.CharField(label='Trigramme', required=False, max_length=3)
    #file_path = forms.CharField(label='Chemin du fichier Excel', max_length=1000, widget=forms.TextInput(attrs={'placeholder': 'C:\\chemin\\vers\\le\\fichier.xlsx'}))
    file_path = forms.FileField(label='Sélectionner le fichier Excel')

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
    name = forms.CharField(label='Nom', required=False)
    short_name = forms.CharField(label='Trigramme', required=False)

class LectureFilterForm(ObjectFilterForm):
    name = forms.CharField(label='Nom', required=False)

class QuestionFilterForm(ObjectFilterForm):
    question = forms.CharField(label='Question', required=False)
    answer = forms.CharField(label='Réponse', required=False)

class QuizzFilterForm(ObjectFilterForm):
    name = forms.CharField(label='Nom', required=False)

class SubjectUpdateForm(forms.ModelForm): 
    class Meta:
        model = Subject
        fields = ['name', 'short_name' ]
        labels = {
            'name': 'Nom',
            'short_name': 'Trigramme',
        }

class LectureUpdateForm(forms.ModelForm): 
    class Meta:
        model = Lecture
        fields = ['name' ]
        labels = {
            'name': 'Nom',
        }

class QuestionUpdateForm(forms.ModelForm): 
    class Meta:
        model = Question
        fields = ['question','answer' ]
        labels = {
            'question': 'Question',
            'answer':'Answer'
        }

class QuizzUpdateForm(forms.ModelForm): 
    class Meta:
        model = Quizz
        fields = ['name','mode','hints']
        labels = {
            'name': 'Nom',
            'mode': 'Mode',
            'hints' : 'Avec indices'
        }

class CreateQuizzForm(forms.Form):
    quizz_name = forms.CharField(label='Nom', required=False)
    max_questions = forms.IntegerField(min_value=1)
    mode = forms.ModelChoiceField(queryset=QuizzMode.objects.all(), label='Mode')
    hints = forms.BooleanField(label = 'Avec indices', initial=True, required=False)