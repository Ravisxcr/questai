import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.contrib import messages
from django.db.models import Avg

from .models import QuizAttempt, AttemptAnswer
from apps.arenas.models import Arena
from apps.questions.models import Question


def start_quiz_view(request, arena_pk):
    """
    Configure and initialize a new quiz attempt for an Arena.
    """
    arena = get_object_or_404(Arena, pk=arena_pk)
    
    # Query parameters for filtering questions
    filter_type = request.POST.get('filter_type', 'ALL').upper()
    limit = int(request.POST.get('limit', 0))

    questions_qs = arena.questions.all()
    if filter_type in ['MCQ', 'SHORT', 'LONG']:
        questions_qs = questions_qs.filter(question_type=filter_type)
        
    if not questions_qs.exists():
        messages.warning(request, "No questions found matching your selection. Please generate questions first.")
        return redirect('arenas:detail', pk=str(arena.id))

    if limit > 0:
        questions_qs = questions_qs.order_by('?')[:limit]
    else:
        questions_qs = questions_qs.order_by('created_at')

    questions_list = list(questions_qs)
    total_mcqs = sum(1 for q in questions_list if q.is_mcq)

    # Create new QuizAttempt
    attempt = QuizAttempt.objects.create(
        arena=arena,
        title=f"{arena.name} ({filter_type})",
        question_filter=filter_type,
        total_questions=len(questions_list),
        total_mcq_count=total_mcqs,
        started_at=timezone.now(),
    )

    # Create empty answer placeholders
    answers = [
        AttemptAnswer(attempt=attempt, question=q)
        for q in questions_list
    ]
    AttemptAnswer.objects.bulk_create(answers)

    return redirect('quizzes:take', pk=str(attempt.id))


def take_quiz_view(request, pk):
    """
    Renders the active quiz testing interface.
    """
    attempt = get_object_or_404(QuizAttempt, pk=pk)
    
    if attempt.is_completed:
        return redirect('quizzes:attempt_result', pk=str(attempt.id))
        
    answers = attempt.answers.select_related('question').all()

    # Serialize questions for interactive React QuizRunner
    questions_data = [
        {
            'id': str(ans.question.id),
            'answer_id': str(ans.id),
            'type': ans.question.question_type,
            'difficulty': ans.question.difficulty,
            'question': ans.question.question_text,
            'options': ans.question.options or [],
            'is_multiagent_verified': ans.question.is_multiagent_verified,
        }
        for ans in answers
    ]

    context = {
        'attempt': attempt,
        'arena': attempt.arena,
        'answers': answers,
        'questions_json': json.dumps(questions_data),
    }
    return render(request, 'quizzes/take_quiz.html', context)


def submit_quiz_view(request, pk):
    """
    Process quiz submission, auto-grade MCQs, calculate duration, and record results.
    """
    attempt = get_object_or_404(QuizAttempt, pk=pk)
    
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    elapsed_seconds = int(request.POST.get('duration_seconds', 0))
    answers = attempt.answers.select_related('question').all()

    correct_mcq_count = 0
    total_mcqs = 0

    for ans in answers:
        q = ans.question
        user_response = request.POST.get(f'question_{q.id}', '').strip()
        ans.user_answer = user_response

        if q.is_mcq:
            total_mcqs += 1
            # Check correctness: match trimmed string or option text
            correct_norm = q.correct_answer.strip().lower()
            user_norm = user_response.strip().lower()

            # Handle case where user clicked e.g. "B) London" or just "London" or option prefix
            is_match = (user_norm == correct_norm)
            if not is_match and len(user_norm) > 3 and user_norm[1:3] == ") ":
                is_match = (user_norm[3:].strip() == correct_norm)
            if not is_match and len(correct_norm) > 3 and correct_norm[1:3] == ") ":
                is_match = (user_norm == correct_norm[3:].strip())

            ans.is_correct = is_match
            if is_match:
                correct_mcq_count += 1
        else:
            # Subjective questions initially marked pending self-evaluation
            ans.is_correct = None

        ans.save(update_fields=['user_answer', 'is_correct'])

    # Finalize attempt stats
    attempt.total_mcq_count = total_mcqs
    attempt.correct_mcq_count = correct_mcq_count
    
    if total_mcqs > 0:
        attempt.score_percentage = round((correct_mcq_count / total_mcqs) * 100, 1)
    else:
        attempt.score_percentage = 100.0  # If only subjective questions, default 100 until self-rated

    attempt.duration_seconds = max(elapsed_seconds, int((timezone.now() - attempt.started_at).total_seconds()))
    attempt.completed_at = timezone.now()
    attempt.save()

    messages.success(request, f"Quiz completed! You scored {attempt.score_percentage:.1f}%.")
    return redirect('quizzes:attempt_result', pk=str(attempt.id))


def attempt_result_view(request, pk):
    """
    Displays comprehensive attempt results, answers comparison, explanations,
    and interactive self-assessment for short/long answers.
    """
    attempt = get_object_or_404(QuizAttempt, pk=pk)
    answers = attempt.answers.select_related('question').all()

    context = {
        'attempt': attempt,
        'arena': attempt.arena,
        'answers': answers,
    }
    return render(request, 'quizzes/attempt_result.html', context)


def self_grade_answer_api(request, pk, answer_pk):
    """
    AJAX endpoint for user self-grading on Short and Long answer questions.
    """
    attempt = get_object_or_404(QuizAttempt, pk=pk)
    answer = get_object_or_404(AttemptAnswer, pk=answer_pk, attempt=attempt)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_correct = data.get('is_correct')
            self_rating = data.get('self_rating')

            if is_correct is not None:
                answer.is_correct = bool(is_correct)
            if self_rating is not None:
                answer.self_rating = int(self_rating)

            answer.save(update_fields=['is_correct', 'self_rating'])

            # Recalculate overall score if user graded subjective answers
            all_answers = attempt.answers.all()
            evaluated = [a for a in all_answers if a.is_correct is not None]
            if evaluated:
                correct_eval = sum(1 for a in evaluated if a.is_correct)
                attempt.score_percentage = round((correct_eval / len(evaluated)) * 100, 1)
                attempt.save(update_fields=['score_percentage'])

            return JsonResponse({
                'success': True,
                'is_correct': answer.is_correct,
                'self_rating': answer.self_rating,
                'updated_score': attempt.score_percentage,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return HttpResponseNotAllowed(['POST'])


def attempt_history_view(request):
    """
    List past attempts across all arenas or filtered by specific arena.
    """
    arena_id = request.GET.get('arena')
    attempts = QuizAttempt.objects.filter(completed_at__isnull=False).select_related('arena')
    
    if arena_id:
        attempts = attempts.filter(arena_id=arena_id)
        
    arenas = Arena.objects.all()

    context = {
        'attempts': attempts,
        'arenas': arenas,
        'selected_arena': arena_id,
    }
    return render(request, 'quizzes/attempt_history.html', context)

