from django.conf import settings

def questai_globals(request):
    """Provide global configuration settings to all templates."""
    return {
        'OLLAMA_BASE_URL': getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434'),
        'OLLAMA_DEFAULT_MODEL': getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama3.2'),
        'CELERY_ALWAYS_EAGER': getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False),
    }

