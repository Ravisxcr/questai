from django.contrib import admin
from .models import Question, GenerationTask


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_truncated', 'arena', 'question_type', 'difficulty', 'created_at')
    search_fields = ('question_text', 'correct_answer', 'arena__name')
    list_filter = ('question_type', 'difficulty', 'created_at')

    def question_text_truncated(self, obj):
        return obj.question_text[:75] + '...' if len(obj.question_text) > 75 else obj.question_text
    question_text_truncated.short_description = 'Question'


@admin.register(GenerationTask)
class GenerationTaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'arena', 'status', 'total_requested', 'generated_count', 'updated_at')
    search_fields = ('task_id', 'arena__name', 'message')
    list_filter = ('status', 'created_at')

