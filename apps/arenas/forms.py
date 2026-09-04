from django import forms
from .models import Arena
from apps.services.ollama_client import get_available_models

SHADCN_INPUT = (
    "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground "
    "ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium "
    "placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 "
    "focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
)

SHADCN_TEXTAREA = (
    "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground "
    "ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 "
    "focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
)

SHADCN_SELECT = (
    "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 "
    "text-sm text-foreground ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring "
    "focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
)


class ArenaForm(forms.ModelForm):
    """Form to create or update an Arena with shadcn styling."""
    class Meta:
        model = Arena
        fields = ['name', 'description', 'color_theme']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': SHADCN_INPUT,
                'placeholder': 'e.g. Operating Systems & Distributed Architecture',
            }),
            'description': forms.Textarea(attrs={
                'class': SHADCN_TEXTAREA,
                'rows': 3,
                'placeholder': 'Optional summary or notes about what this arena is studying...',
            }),
            'color_theme': forms.Select(attrs={
                'class': SHADCN_SELECT,
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
    initial question generation parameters with shadcn styling.
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
            'class': 'block w-full text-xs text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:opacity-90 cursor-pointer',
        })
    )
    
    mcq_count = forms.IntegerField(
        label="MCQ Questions",
        initial=3,
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(attrs={'class': SHADCN_INPUT})
    )

    short_count = forms.IntegerField(
        label="Short Answer Questions",
        initial=2,
        min_value=0,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': SHADCN_INPUT})
    )

    long_count = forms.IntegerField(
        label="Long / Essay Questions",
        initial=1,
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': SHADCN_INPUT})
    )

    difficulty = forms.ChoiceField(
        label="Difficulty Level",
        choices=DIFFICULTY_CHOICES,
        initial='MEDIUM',
        widget=forms.Select(attrs={'class': SHADCN_SELECT})
    )

    model_name = forms.CharField(
        label="Ollama Model",
        required=False,
        widget=forms.TextInput(attrs={
            'class': SHADCN_INPUT,
            'placeholder': 'e.g. llama3.2, mistral, phi3',
        })
    )

    def clean_pdf_files(self):
        files = self.cleaned_data.get('pdf_files')
        for f in files:
            if not f.name.lower().endswith('.pdf'):
                raise forms.ValidationError(f"File '{f.name}' is not a valid PDF document.")
        return files
