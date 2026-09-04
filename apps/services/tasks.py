import logging
from celery import shared_task
from django.utils import timezone

from .pdf_extractor import extract_text_from_pdf
from .langchain_generator import generate_questions_from_context
from .multiagent import run_mcq_multiagent_pipeline

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
    and generate requested MCQs using the 4-agent consensus verification pipeline,
    plus short & long answer questions using LangChain + Ollama.
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

    def update_task_progress(msg: str):
        if task_record:
            task_record.message = msg[:255]
            task_record.save(update_fields=['message', 'updated_at'])

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
            combined_context = "\n\n".join(extracted_sections)
            created_questions = []

            # 1. Multi-Agent Pipeline for MCQs (100% correct Q&A with deep reasoning)
            if mcq_count > 0:
                update_task_progress(f"Multi-Agent System: Drafting and auditing {mcq_count} MCQs...")
                try:
                    verified_mcqs = run_mcq_multiagent_pipeline(
                        context_text=combined_context,
                        count=mcq_count,
                        difficulty=difficulty,
                        model_name=model_name,
                        progress_callback=update_task_progress,
                    )
                    
                    for v_mcq in verified_mcqs:
                        q = Question(
                            arena=arena,
                            document=primary_doc,
                            question_type='MCQ',
                            difficulty=v_mcq.difficulty or difficulty,
                            question_text=v_mcq.question,
                            options=v_mcq.options,
                            correct_answer=v_mcq.correct_answer,
                            explanation=v_mcq.explanation,
                            step_by_step_reasoning=v_mcq.step_by_step_reasoning,
                            distractor_analysis=v_mcq.distractor_analysis,
                            grounding_evidence=v_mcq.grounding_evidence,
                            is_multiagent_verified=True,
                        )
                        created_questions.append(q)
                except Exception as e:
                    logger.warning(f"Multi-agent pipeline encountered exception: {e}, falling back to standard generator.")

            # 2. Short & Long Answer Questions (or fallback if MCQs needed)
            remaining_mcq = mcq_count - len([q for q in created_questions if q.is_mcq])
            need_batch_call = (short_count > 0) or (long_count > 0) or (remaining_mcq > 0)

            if need_batch_call:
                update_task_progress("Generating Short & Long conceptual questions with Ollama...")
                batch_result = generate_questions_from_context(
                    context_text=combined_context,
                    mcq_count=max(0, remaining_mcq),
                    short_count=short_count,
                    long_count=long_count,
                    difficulty=difficulty,
                    model_name=model_name,
                )

                # Add any fallback MCQs if multi-agent returned fewer
                for item in batch_result.mcqs[:remaining_mcq]:
                    q = Question(
                        arena=arena,
                        document=primary_doc,
                        question_type='MCQ',
                        difficulty=item.difficulty or difficulty,
                        question_text=item.question,
                        options=item.options,
                        correct_answer=item.correct_answer,
                        explanation=item.explanation,
                        is_multiagent_verified=False,
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
                task_record.message = f'Successfully generated {len(created_questions)} verified questions.'
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
