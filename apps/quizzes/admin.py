from django.contrib import admin
from .models import QuizAttempt, AttemptAnswer


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    fields = ('question', 'user_answer', 'is_correct', 'self_rating')
    readonly_fields = ('question',)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('title', 'arena', 'question_filter', 'score_percentage', 'grade', 'duration_seconds', 'completed_at')
    search_fields = ('title', 'arena__name')
    list_filter = ('question_filter', 'started_at', 'completed_at')
    inlines = [AttemptAnswerInline]

