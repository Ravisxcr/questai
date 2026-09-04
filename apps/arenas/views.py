import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse

from .models import Arena, Document
from .forms import ArenaForm, DocumentUploadAndGenerateForm
from apps.questions.models import Question, GenerationTask
from apps.services.tasks import process_arena_documents_task
from apps.services.ollama_client import get_available_models, get_ollama_status


def arena_list_view(request):
    """
    List all Arenas in a NotebookLM card-based workspace layout.
    Supports text search.
    """
    query = request.GET.get('q', '').strip()
    arenas = Arena.objects.all()
    
    if query:
        arenas = arenas.filter(Q(name__icontains=query) | Q(description__icontains=query))
        
    form = ArenaForm()
    ollama_info = get_ollama_status()
    
    context = {
        'arenas': arenas,
        'form': form,
        'search_query': query,
        'ollama_info': ollama_info,
    }
    return render(request, 'arenas/arena_list.html', context)


def arena_create_view(request):
    """Create a new Arena."""
    if request.method == 'POST':
        form = ArenaForm(request.POST)
        if form.is_valid():
            arena = form.save()
            messages.success(request, f'Arena "{arena.name}" created successfully.')
            return redirect('arenas:detail', pk=str(arena.id))
        else:
            messages.error(request, 'Please check the form inputs.')
    return redirect('arenas:list')


def arena_update_view(request, pk):
    """Update Arena name, description, or color theme."""
    arena = get_object_or_404(Arena, pk=pk)
    if request.method == 'POST':
        form = ArenaForm(request.POST, instance=arena)
        if form.is_valid():
            form.save()
            messages.success(request, 'Arena updated successfully.')
            return redirect('arenas:detail', pk=str(arena.id))
    else:
        form = ArenaForm(instance=arena)
        
    return render(request, 'arenas/arena_form.html', {'form': form, 'arena': arena})


def arena_delete_view(request, pk):
    """Delete an Arena and all associated content."""
    arena = get_object_or_404(Arena, pk=pk)
    if request.method == 'POST':
        name = arena.name
        arena.delete()
        messages.success(request, f'Arena "{name}" and all its contents were deleted.')
        return redirect('arenas:list')
    return render(request, 'arenas/arena_confirm_delete.html', {'arena': arena})


def arena_detail_view(request, pk):
    """
    NotebookLM-style workspace for an Arena:
    - Sources panel (PDF documents)
    - Question viewer with type filters (All, MCQ, Short, Long)
    - Quiz quick launcher & recent attempts history
    """
    arena = get_object_or_404(Arena, pk=pk)
    documents = arena.documents.all()
    
    # Filter questions by type if requested
    q_type = request.GET.get('type', 'ALL').upper()
    questions = arena.questions.all()
    if q_type in ['MCQ', 'SHORT', 'LONG']:
        questions = questions.filter(question_type=q_type)
        
    # Search within questions
    q_search = request.GET.get('q', '').strip()
    if q_search:
        questions = questions.filter(
            Q(question_text__icontains=q_search) |
            Q(correct_answer__icontains=q_search) |
            Q(explanation__icontains=q_search)
        )
        
    recent_attempts = arena.attempts.all()[:5]
    latest_task = arena.generation_tasks.first()
    
    upload_form = DocumentUploadAndGenerateForm()
    available_models = get_available_models()
    ollama_info = get_ollama_status()

    # Serialize questions for interactive React QuestionExplorer
    all_arena_questions = arena.questions.all()
    questions_data = [
        {
            'id': str(q.id),
            'type': q.question_type,
            'difficulty': q.difficulty,
            'question': q.question_text,
            'options': q.options or [],
            'correct_answer': q.correct_answer,
            'explanation': q.explanation,
            'key_points': q.key_points or [],
            'step_by_step_reasoning': q.step_by_step_reasoning,
            'distractor_analysis': q.distractor_analysis or {},
            'grounding_evidence': q.grounding_evidence,
            'is_multiagent_verified': q.is_multiagent_verified,
            'created_at': q.created_at.strftime("%b %d, %Y"),
        }
        for q in all_arena_questions
    ]

    context = {
        'arena': arena,
        'documents': documents,
        'questions': questions,
        'questions_json': json.dumps(questions_data),
        'selected_type': q_type,
        'search_query': q_search,
        'recent_attempts': recent_attempts,
        'latest_task': latest_task,
        'upload_form': upload_form,
        'available_models': available_models,
        'ollama_info': ollama_info,
    }
    return render(request, 'arenas/arena_detail.html', context)


def document_upload_view(request, pk):
    """
    Upload one or more PDFs to the Arena and trigger background extraction + AI generation.
    """
    arena = get_object_or_404(Arena, pk=pk)
    
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
        
    form = DocumentUploadAndGenerateForm(request.POST, request.FILES)
    if not form.is_valid():
        error_msgs = "; ".join([f"{k}: {', '.join(v)}" for k, v in form.errors.items()])
        messages.error(request, f"Upload error: {error_msgs}")
        return redirect('arenas:detail', pk=str(arena.id))
        
    pdf_files = form.cleaned_data['pdf_files']
    mcq_count = form.cleaned_data.get('mcq_count', 3)
    short_count = form.cleaned_data.get('short_count', 2)
    long_count = form.cleaned_data.get('long_count', 1)
    difficulty = form.cleaned_data.get('difficulty', 'MEDIUM')
    model_name = form.cleaned_data.get('model_name') or None

    created_docs = []
    for f in pdf_files:
        doc = Document.objects.create(
            arena=arena,
            file=f,
            filename=f.name,
            file_size=f.size,
            status='PENDING',
        )
        created_docs.append(doc)

    total_requested = mcq_count + short_count + long_count
    
    # Create tracking record
    gen_task = GenerationTask.objects.create(
        task_id=str(uuid.uuid4()),
        arena=arena,
        status='PENDING',
        total_requested=total_requested,
        message='Queued for processing...',
    )

    doc_ids = [str(d.id) for d in created_docs]
    gen_params = {
        'mcq_count': mcq_count,
        'short_count': short_count,
        'long_count': long_count,
        'difficulty': difficulty,
        'model_name': model_name,
    }

    # Dispatch Celery task
    process_arena_documents_task.delay(
        arena_id=str(arena.id),
        document_ids=doc_ids,
        generation_params=gen_params,
        task_record_id=str(gen_task.id),
    )

    messages.success(
        request,
        f"Uploaded {len(created_docs)} document(s). Processing text & generating {total_requested} questions in background."
    )
    return redirect('arenas:detail', pk=str(arena.id))


def document_delete_view(request, pk, doc_pk):
    """Delete a specific PDF document from an Arena."""
    arena = get_object_or_404(Arena, pk=pk)
    doc = get_object_or_404(Document, pk=doc_pk, arena=arena)
    
    if request.method == 'POST':
        filename = doc.filename
        # Delete file from storage
        if doc.file:
            doc.file.delete(save=False)
        doc.delete()
        messages.success(request, f"Document '{filename}' deleted.")
    return redirect('arenas:detail', pk=str(arena.id))


def task_status_api(request, pk, task_id):
    """
    JSON endpoint for client-side live polling of background generation tasks.
    """
    arena = get_object_or_404(Arena, pk=pk)
    task = get_object_or_404(GenerationTask, task_id=task_id, arena=arena)
    
    return JsonResponse({
        'task_id': task.task_id,
        'status': task.status,
        'message': task.message,
        'total_requested': task.total_requested,
        'generated_count': task.generated_count,
        'error_detail': task.error_detail,
        'updated_at': task.updated_at.isoformat(),
    })

