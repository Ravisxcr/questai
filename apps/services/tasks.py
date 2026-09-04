import logging
from celery import shared_task
from django.utils import timezone

from .pdf_extractor import extract_text_from_pdf
from .langchain_generator import generate_questions_from_context

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_arena_documents_task(
    self,
    arena_id: str,
    document_ids: list,
    generation_params: dict = None,
    task_record_id: str = None,
):
    """
    Background Celery task to extract text from uploaded PDFs
    and generate requested MCQs, short answers, and long answers using LangChain + Ollama.
    """
    from apps.arenas.models import Arena, Document
    from apps.questions.models import Question, GenerationTask

    # Retrieve task record if created
    task_record = None
    if task_record_id:
        try:
            task_record = GenerationTask.objects.get(id=task_record_id)
            task_record.status = 'STARTED'
            task_record.message = 'Extracting text from PDF documents...'
            task_record.save(update_fields=['status', 'message', 'updated_at'])
        except GenerationTask.DoesNotExist:
            task_record = None

    try:
        arena = Arena.objects.get(id=arena_id)
        documents = Document.objects.filter(id__in=document_ids, arena=arena)
        
        extracted_sections = []
        primary_doc = documents.first() if documents.exists() else None

        for doc in documents:
            doc.status = 'PROCESSING'
            doc.save(update_fields=['status'])
            
            try:
                extraction_result = extract_text_from_pdf(doc.file.path)
                
                if extraction_result["error"]:
                    doc.status = 'FAILED'
                    doc.error_message = extraction_result["error"]
                    doc.save(update_fields=['status', 'error_message'])
                    logger.warning(f"Error extracting PDF for doc {doc.id}: {extraction_result['error']}")
                else:
                    doc.page_count = extraction_result["page_count"]
                    doc.extracted_text = extraction_result["full_text"]
                    doc.status = 'COMPLETED'
                    doc.error_message = ""
                    doc.save(update_fields=['page_count', 'extracted_text', 'status', 'error_message'])
                    
                    if doc.extracted_text:
                        extracted_sections.append(f"--- Document: {doc.filename} ---\n{doc.extracted_text}")

            except Exception as e:
                doc.status = 'FAILED'
                doc.error_message = str(e)
                doc.save(update_fields=['status', 'error_message'])
                logger.error(f"Exception during extraction of {doc.id}: {e}")

        # If question generation was requested
        generation_params = generation_params or {}
        mcq_count = generation_params.get('mcq_count', 0)
        short_count = generation_params.get('short_count', 0)
        long_count = generation_params.get('long_count', 0)
        difficulty = generation_params.get('difficulty', 'MEDIUM')
        model_name = generation_params.get('model_name') or None

        total_to_generate = mcq_count + short_count + long_count

        if total_to_generate > 0 and extracted_sections:
            if task_record:
                task_record.message = f'Generating {total_to_generate} questions using Ollama...'
                task_record.save(update_fields=['message', 'updated_at'])

            combined_context = "\n\n".join(extracted_sections)

            # Invoke LangChain AI generator
            batch_result = generate_questions_from_context(
                context_text=combined_context,
                mcq_count=mcq_count,
                short_count=short_count,
                long_count=long_count,
                difficulty=difficulty,
                model_name=model_name,
            )

            created_questions = []

            # Save MCQs
            for item in batch_result.mcqs:
                q = Question(
                    arena=arena,
                    document=primary_doc,
                    question_type='MCQ',
                    difficulty=item.difficulty or difficulty,
                    question_text=item.question,
                    options=item.options,
                    correct_answer=item.correct_answer,
                    explanation=item.explanation,
                )
                created_questions.append(q)

            # Save Short Answers
            for item in batch_result.short_answers:
                q = Question(
                    arena=arena,
                    document=primary_doc,
                    question_type='SHORT',
                    difficulty=item.difficulty or difficulty,
                    question_text=item.question,
                    correct_answer=item.ideal_answer,
                    explanation=item.explanation,
                    key_points=item.key_points,
                )
                created_questions.append(q)

            # Save Long Answers
            for item in batch_result.long_answers:
                q = Question(
                    arena=arena,
                    document=primary_doc,
                    question_type='LONG',
                    difficulty=item.difficulty or difficulty,
                    question_text=item.question,
                    correct_answer=item.sample_answer,
                    explanation=item.explanation,
                    key_points=item.key_points,
                )
                created_questions.append(q)

            if created_questions:
                Question.objects.bulk_create(created_questions)

            if task_record:
                task_record.status = 'SUCCESS'
                task_record.generated_count = len(created_questions)
                task_record.message = f'Successfully generated {len(created_questions)} questions.'
                task_record.save(update_fields=['status', 'generated_count', 'message', 'updated_at'])

            return {
                "status": "SUCCESS",
                "arena_id": arena_id,
                "questions_generated": len(created_questions),
            }

        else:
            if task_record:
                task_record.status = 'SUCCESS'
                task_record.generated_count = 0
                task_record.message = 'Text extracted successfully. No questions requested.'
                task_record.save(update_fields=['status', 'generated_count', 'message', 'updated_at'])

            return {
                "status": "SUCCESS",
                "arena_id": arena_id,
                "questions_generated": 0,
            }

    except Exception as e:
        logger.error(f"Error in process_arena_documents_task: {e}", exc_info=True)
        if task_record:
            task_record.status = 'FAILURE'
            task_record.message = 'Task failed.'
            task_record.error_detail = str(e)
            task_record.save(update_fields=['status', 'message', 'error_detail', 'updated_at'])
        return {
            "status": "FAILURE",
            "arena_id": arena_id,
            "error": str(e),
        }

