from django.contrib import admin
from .models import Arena, Document


@admin.register(Arena)
class ArenaAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_theme', 'total_documents', 'total_questions', 'total_attempts', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('color_theme', 'created_at')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'arena', 'page_count', 'formatted_size', 'status', 'created_at')
    search_fields = ('filename', 'arena__name')
    list_filter = ('status', 'created_at')

