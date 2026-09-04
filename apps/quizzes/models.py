import uuid
from django.db import models
from django.urls import reverse


class QuizAttempt(models.Model):
    """
    Records an interactive quiz attempt by the user on questions in an Arena.
    Tracks start time, completion time, duration, and score results.
    """
    FILTER_CHOICES = [
        ('ALL', 'All Question Types'),
        ('MCQ', 'Multiple Choice Only'),
        ('SHORT', 'Short Answer Only'),
        ('LONG', 'Long Answer Only'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    arena = models.ForeignKey('arenas.Arena', on_delete=models.CASCADE, related_name='attempts')
    title = models.CharField(max_length=255, default="Practice Quiz Attempt")
    question_filter = models.CharField(max_length=20, choices=FILTER_CHOICES, default='ALL')
    total_questions = models.IntegerField(default=0)
    total_mcq_count = models.IntegerField(default=0)
    correct_mcq_count = models.IntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Attempt {self.id.hex[:6]} - {self.arena.name} ({self.score_percentage:.1f}%)"

    def get_absolute_url(self):
        return reverse('quizzes:attempt_result', kwargs={'pk': str(self.id)})

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    @property
    def formatted_duration(self) -> str:
        """Returns duration formatted like '2m 35s'."""
        secs = self.duration_seconds
        mins = secs // 60
        rem_secs = secs % 60
        if mins == 0:
            return f"{rem_secs}s"
        return f"{mins}m {rem_secs}s"

    @property
    def grade(self) -> str:
        """Letter grade based on percentage score."""
        score = self.score_percentage
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        return 'F'


class AttemptAnswer(models.Model):
    """
    Records the user's answer to a specific question during a QuizAttempt.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE)
    user_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    self_rating = models.IntegerField(null=True, blank=True, help_text="User self-score (1-5) for subjective questions")
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['question__created_at']

    def __str__(self):
        return f"Answer for {self.question.id.hex[:6]} in attempt {self.attempt.id.hex[:6]}"

