from django import forms
from .models import Arena
from apps.services.ollama_client import get_available_models


class ArenaForm(forms.ModelForm):
    """Form to create or update an Arena."""
    class Meta:
        model = Arena
        fields = ['name', 'description', 'color_theme']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'placeholder': 'e.g. Operating Systems & Distributed Architecture',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'rows': 3,
                'placeholder': 'Optional summary or notes about what this arena is studying...',
            }),
            'color_theme': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none',
            }),
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class DocumentUploadAndGenerateForm(forms.Form):
    """
    Form to upload one or more PDFs to an Arena and optionally configure
    initial question generation parameters.
    """
    DIFFICULTY_CHOICES = [
        ('MEDIUM', 'Medium (Balanced conceptual & analytical)'),
        ('EASY', 'Easy (Foundational & factual)'),
        ('HARD', 'Hard (Advanced & in-depth)'),
        ('MIXED', 'Mixed (Graduated difficulty)'),
    ]

    pdf_files = MultipleFileField(
        label="Select PDF Documents",
        required=True,
        widget=MultipleFileInput(attrs={
            'accept': 'application/pdf',
            'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-indigo-950 dark:file:text-indigo-300 cursor-pointer',
        })
    )
    
    mcq_count = forms.IntegerField(
        label="MCQ Questions",
        initial=3,
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
        })
    )

    short_count = forms.IntegerField(
        label="Short Answer Questions",
        initial=2,
        min_value=0,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
        })
    )

    long_count = forms.IntegerField(
        label="Long / Essay Questions",
        initial=1,
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
        })
    )

    difficulty = forms.ChoiceField(
        label="Difficulty Level",
        choices=DIFFICULTY_CHOICES,
        initial='MEDIUM',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
        })
    )

    model_name = forms.CharField(
        label="Ollama Model",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white',
            'placeholder': 'e.g. llama3.2, mistral, phi3',
        })
    )

    def clean_pdf_files(self):
        files = self.cleaned_data.get('pdf_files')
        for f in files:
            if not f.name.lower().endswith('.pdf'):
                raise forms.ValidationError(f"File '{f.name}' is not a valid PDF document.")
        return files

