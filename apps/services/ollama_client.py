import requests
from typing import Dict, Any, List
from django.conf import settings


def get_ollama_status() -> Dict[str, Any]:
    """
    Check if Ollama server is reachable and fetch available models.
    """
    base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
    tags_url = f"{base_url}/api/tags"
    
    try:
        response = requests.get(tags_url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            models_raw = data.get('models', [])
            models_list = [m.get('name') for m in models_raw if m.get('name')]
            return {
                "connected": True,
                "base_url": base_url,
                "models": models_list,
                "default_model": getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama3.2'),
                "error": None
            }
        else:
            return {
                "connected": False,
                "base_url": base_url,
                "models": [],
                "default_model": getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama3.2'),
                "error": f"Ollama returned HTTP status {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "connected": False,
            "base_url": base_url,
            "models": [],
            "default_model": getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama3.2'),
            "error": f"Could not connect to Ollama at {base_url}. Make sure Ollama is running (`ollama serve`). Details: {str(e)}"
        }


def get_available_models() -> List[str]:
    """Get list of model names currently available in local Ollama."""
    status = get_ollama_status()
    if status["connected"] and status["models"]:
        return status["models"]
    # Fallback to recommended standard defaults
    return [getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama3.2'), 'mistral', 'phi3', 'gemma2']

