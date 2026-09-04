import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages

from .models import Question
from apps.arenas.models import Arena


def question_delete_view(request, pk):
    """Delete a single question."""
    question = get_object_or_404(Question, pk=pk)
    arena_id = question.arena.id
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
    return redirect('arenas:detail', pk=str(arena_id))


def export_questions_view(request, arena_pk, format='json'):
    """
    Export all questions of an arena as JSON or Markdown.
    """
    arena = get_object_or_404(Arena, pk=arena_pk)
    questions = arena.questions.all().order_by('created_at')

    if format == 'markdown':
        content_lines = [f"# {arena.name} - Question Bank\n"]
        if arena.description:
            content_lines.append(f"> {arena.description}\n\n")

        for idx, q in enumerate(questions, 1):
            content_lines.append(f"### Q{idx} [{q.question_type} - {q.difficulty}]\n")
            content_lines.append(f"**Question:** {q.question_text}\n\n")
            
            if q.is_mcq and q.options:
                content_lines.append("**Options:**\n")
                for opt in q.options:
                    content_lines.append(f"- {opt}\n")
                content_lines.append("\n")

            content_lines.append(f"<details><summary><b>View Answer</b></summary>\n\n")
            content_lines.append(f"**Correct Answer:** {q.correct_answer}\n\n")
            if q.explanation:
                content_lines.append(f"**Explanation:** {q.explanation}\n\n")
            if q.key_points:
                content_lines.append(f"**Key Concepts:** {', '.join(q.key_points)}\n\n")
            content_lines.append("</details>\n\n---\n")

        md_content = "".join(content_lines)
        response = HttpResponse(md_content, content_type='text/markdown')
        response['Content-Disposition'] = f'attachment; filename="{arena.name.lower().replace(" ", "_")}_questions.md"'
        return response

    else:
        # JSON format
        data = {
            'arena': arena.name,
            'description': arena.description,
            'total_questions': questions.count(),
            'questions': []
        }
        for q in questions:
            data['questions'].append({
                'id': str(q.id),
                'type': q.question_type,
                'difficulty': q.difficulty,
                'question': q.question_text,
                'options': q.options,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'key_points': q.key_points,
            })
            
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{arena.name.lower().replace(" ", "_")}_questions.json"'
        return response

