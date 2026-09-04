import json
from django.shortcuts import render
from django.db.models import Avg, Sum, Count, Max
from apps.arenas.models import Arena, Document
from apps.questions.models import Question
from apps.quizzes.models import QuizAttempt


def dashboard_view(request):
    """
    Renders comprehensive analytics dashboard with visual metrics and charts.
    """
    total_arenas = Arena.objects.count()
    total_documents = Document.objects.count()
    total_questions = Question.objects.count()
    
    attempts = QuizAttempt.objects.filter(completed_at__isnull=False)
    total_attempts = attempts.count()
    
    # Average score
    avg_score_agg = attempts.aggregate(Avg('score_percentage'))['score_percentage__avg']
    avg_score = round(avg_score_agg or 0.0, 1)

    # Study time
    total_seconds_agg = attempts.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
    hours = total_seconds_agg // 3600
    minutes = (total_seconds_agg % 3600) // 60
    study_time_display = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    # Question types breakdown
    mcq_count = Question.objects.filter(question_type='MCQ').count()
    short_count = Question.objects.filter(question_type='SHORT').count()
    long_count = Question.objects.filter(question_type='LONG').count()

    # Difficulty breakdown
    easy_count = Question.objects.filter(difficulty='EASY').count()
    medium_count = Question.objects.filter(difficulty='MEDIUM').count()
    hard_count = Question.objects.filter(difficulty='HARD').count()

    # Attempts timeline data (last 15 completed attempts ordered chronologically)
    recent_attempts = attempts.order_by('started_at')[:15]
    chart_labels = []
    chart_scores = []
    for att in recent_attempts:
        chart_labels.append(att.started_at.strftime("%b %d, %H:%M"))
        chart_scores.append(round(att.score_percentage, 1))

    # Arena performance table
    arenas_list = Arena.objects.annotate(
        doc_count=Count('documents', distinct=True),
        q_count=Count('questions', distinct=True),
        att_count=Count('attempts', distinct=True),
    ).order_by('-updated_at')

    arena_stats = []
    arena_names = []
    arena_avg_scores = []
    
    for ar in arenas_list:
        completed_atts = ar.attempts.filter(completed_at__isnull=False)
        avg = completed_atts.aggregate(Avg('score_percentage'))['score_percentage__avg']
        best = completed_atts.aggregate(Max('score_percentage'))['score_percentage__max']
        avg_val = round(avg or 0.0, 1)
        best_val = round(best or 0.0, 1)
        
        arena_stats.append({
            'arena': ar,
            'doc_count': ar.doc_count,
            'q_count': ar.q_count,
            'att_count': ar.att_count,
            'avg_score': avg_val,
            'best_score': best_val,
        })
        arena_names.append(ar.name)
        arena_avg_scores.append(avg_val)

    context = {
        'total_arenas': total_arenas,
        'total_documents': total_documents,
        'total_questions': total_questions,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
        'study_time_display': study_time_display,
        'mcq_count': mcq_count,
        'short_count': short_count,
        'long_count': long_count,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'arena_stats': arena_stats,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_scores_json': json.dumps(chart_scores),
        'arena_names_json': json.dumps(arena_names[:8]),
        'arena_avg_scores_json': json.dumps(arena_avg_scores[:8]),
    }

    return render(request, 'analytics/dashboard.html', context)

