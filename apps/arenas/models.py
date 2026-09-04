import uuid
from django.db import models
from django.urls import reverse


class Arena(models.Model):
    """
    An isolated workspace containing related PDF documents, questions, and attempts.
    Inspired by NotebookLM notebooks.
    """
    COLOR_CHOICES = [
        ('indigo', 'Indigo'),
        ('emerald', 'Emerald'),
        ('amber', 'Amber'),
        ('rose', 'Rose'),
        ('sky', 'Sky'),
        ('violet', 'Violet'),
        ('teal', 'Teal'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Name of the Arena / Notebook")
    description = models.TextField(blank=True, help_text="Brief description or topic summary")
    color_theme = models.CharField(max_length=30, choices=COLOR_CHOICES, default='indigo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('arenas:detail', kwargs={'pk': str(self.id)})

    @property
    def total_documents(self) -> int:
        return self.documents.count()

    @property
    def total_questions(self) -> int:
        return self.questions.count()

    @property
    def total_attempts(self) -> int:
        return self.attempts.count()

    @property
    def average_score(self) -> float:
        attempts = self.attempts.filter(completed_at__isnull=False)
        if not attempts.exists():
            return 0.0
        avg = attempts.aggregate(models.Avg('score_percentage'))['score_percentage__avg']
        return round(avg or 0.0, 1)


class Document(models.Model):
    """
    A PDF document uploaded to an Arena.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Extraction'),
        ('PROCESSING', 'Extracting Text & Generating'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    arena = models.ForeignKey(Arena, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='arena_documents/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0, help_text="File size in bytes")
    page_count = models.IntegerField(default=0)
    extracted_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} ({self.arena.name})"

    @property
    def formatted_size(self) -> str:
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

