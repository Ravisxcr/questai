import json
import re
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from .schemas import QuestionBatchSchema, MCQItem, ShortAnswerItem, LongAnswerItem

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[dict]:
    """Extract and parse JSON object from raw LLM output, handling markdown blocks."""
    if not text:
        return None

    # Try 1: Direct JSON parsing
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try 2: Markdown ```json ... ``` blocks
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try 3: Find first '{' and last '}'
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    return None


def get_llm(model_name: Optional[str] = None, temperature: float = 0.3) -> ChatOllama:
    """Instantiate a ChatOllama LLM instance."""
    base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
    selected_model = model_name or getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama3.2')
    timeout = getattr(settings, 'OLLAMA_TIMEOUT', 120)

    return ChatOllama(
        base_url=base_url,
        model=selected_model,
        temperature=temperature,
        timeout=timeout,
    )


def generate_questions_from_context(
    context_text: str,
    mcq_count: int = 3,
    short_count: int = 2,
    long_count: int = 1,
    difficulty: str = "MEDIUM",
    model_name: Optional[str] = None,
) -> QuestionBatchSchema:
    """
    Generate MCQs, short answer, and long answer questions based on the provided context.
    
    Args:
        context_text: Extracted text from PDF documents.
        mcq_count: Number of multiple-choice questions to generate.
        short_count: Number of short-answer questions to generate.
        long_count: Number of long-answer questions to generate.
        difficulty: EASY, MEDIUM, HARD, or MIXED.
        model_name: Ollama model name to use.
        
    Returns:
        QuestionBatchSchema containing structured lists of questions.
    """
    # Truncate context to ~12,000 characters if too large to fit in typical local model context
    safe_context = context_text[:14000] if len(context_text) > 14000 else context_text

    llm = get_llm(model_name=model_name)
    parser = PydanticOutputParser(pydantic_object=QuestionBatchSchema)

    system_instructions = (
        "You are an expert academic educator and assessment specialist. "
        "Your task is to generate high-quality educational questions strictly based on the provided document text. "
        "Ensure all questions are directly answerable using only the information in the text.\n\n"
        "Requirements:\n"
        f"- Multiple Choice Questions (MCQ): Generate exactly {mcq_count} questions. Each must have exactly 4 options, a clearly marked correct option, and an explanation.\n"
        f"- Short Answer Questions: Generate exactly {short_count} conceptual questions. Each must have a concise model answer (1-3 sentences) and key points/keywords.\n"
        f"- Long Answer Questions: Generate exactly {long_count} analytical/essay questions. Each must have a comprehensive sample answer, grading rubric, and key concepts.\n"
        f"- Difficulty Level: {difficulty}.\n\n"
        "OUTPUT FORMAT REQUIREMENTS:\n"
        "You MUST respond ONLY with a valid, parseable JSON object matching the schema below. "
        "Do NOT include any preamble, commentary, greetings, or explanations outside the JSON structure.\n\n"
        "{format_instructions}"
    )

    human_prompt = (
        "Document Context:\n"
        "\"\"\"\n"
        "{context}\n"
        "\"\"\"\n\n"
        "Generate the requested questions based on the context above. Output strictly JSON."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("human", human_prompt),
    ])

    formatted_prompt = prompt.format_prompt(
        context=safe_context,
        format_instructions=parser.get_format_instructions(),
    )

    try:
        response = llm.invoke(formatted_prompt.to_messages())
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Attempt 1: PydanticOutputParser
        try:
            return parser.parse(response_text)
        except Exception:
            pass

        # Attempt 2: Extract JSON and validate with Pydantic
        extracted_json = extract_json_from_text(response_text)
        if extracted_json:
            return QuestionBatchSchema.model_validate(extracted_json)

        # Attempt 3: If parsing completely fails, return empty container
        logger.warning(f"Could not parse LLM output as JSON: {response_text[:300]}")
        return QuestionBatchSchema(
            title="Generated Questions",
            summary="Questions generated from document context",
            mcqs=[],
            short_answers=[],
            long_answers=[],
        )

    except Exception as e:
        logger.error(f"Error invoking LangChain Ollama generator: {e}")
        raise e

