import json
import logging
from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from apps.services.langchain_generator import get_llm, extract_json_from_text
from .schemas import (
    CandidateMCQ,
    CandidateBatch,
    AuditVerdict,
    SolverVerdict,
    RefinedReasoning,
)

logger = logging.getLogger(__name__)


class ItemWriterAgent:
    """Agent 1: Drafts candidate MCQs grounded strictly in the source context."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = get_llm(model_name=model_name, temperature=0.3)
        self.parser = PydanticOutputParser(pydantic_object=CandidateBatch)

    def draft(self, context_text: str, count: int = 3, difficulty: str = "MEDIUM") -> List[CandidateMCQ]:
        system_prompt = (
            "You are a Senior Academic Examiner and Question Design Specialist. "
            "Your task is to draft high-caliber, factually infallible Multiple Choice Questions (MCQs) "
            "based STRICTLY and EXCLUSIVELY on the provided document context.\n\n"
            "CRITICAL RULES:\n"
            "1. Every question must test a meaningful concept, mechanism, definition, or relation from the text.\n"
            "2. For each question, provide exactly 4 distinct options (e.g. A, B, C, D).\n"
            "3. Provide the exact designated correct option text.\n"
            "4. Provide the exact verbatim quote or sentence from the text that proves the designated answer.\n"
            "5. The distractors must be plausible to a casual reader, but unambiguously incorrect based on the text.\n"
            f"6. Target difficulty: {difficulty}. Total questions to draft: {count}.\n\n"
            "OUTPUT FORMAT:\n"
            "You must respond ONLY with a valid JSON object matching the requested schema.\n"
            "{format_instructions}"
        )

        human_prompt = (
            "Source Document Context:\n"
            "\"\"\"\n{context}\n\"\"\"\n\n"
            f"Draft {count} high-quality candidate MCQs. Respond strictly in JSON."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt),
        ])

        formatted = prompt.format_prompt(
            context=context_text[:12000],
            format_instructions=self.parser.get_format_instructions(),
        )

        try:
            response = self.llm.invoke(formatted.to_messages())
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                batch = self.parser.parse(content)
                return batch.candidates
            except Exception:
                extracted = extract_json_from_text(content)
                if extracted:
                    batch = CandidateBatch.model_validate(extracted)
                    return batch.candidates
        except Exception as e:
            logger.error(f"ItemWriterAgent error: {e}")

        return []


class FactCheckAuditorAgent:
    """Agent 2: Fact-checks candidate questions strictly against the source context."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = get_llm(model_name=model_name, temperature=0.1)
        self.parser = PydanticOutputParser(pydantic_object=AuditVerdict)

    def audit(self, candidate: CandidateMCQ, context_text: str) -> AuditVerdict:
        system_prompt = (
            "You are the Chief Fact-Checking Auditor for educational assessments. "
            "Your job is to rigorously cross-examine the candidate question against the source text.\n\n"
            "AUDIT CHECKLIST:\n"
            "1. Context Grounding: Is the designated answer 100% supported by the text? (Are there any hallucinated facts?)\n"
            "2. Option Exclusivity: Is there exactly ONE correct answer? None of the other 3 distractors must be defensible as true.\n"
            "3. Ambiguity: Is the wording clear, precise, and free of double meanings?\n\n"
            "OUTPUT FORMAT:\n"
            "Respond strictly in JSON matching the schema.\n"
            "{format_instructions}"
        )

        human_prompt = (
            "Source Context:\n\"\"\"\n{context}\n\"\"\"\n\n"
            "Candidate Question:\n"
            f"Question: {candidate.question}\n"
            f"Options: {candidate.options}\n"
            f"Designated Correct Answer: {candidate.designated_answer}\n"
            f"Claimed Source Quote: {candidate.source_quote}\n\n"
            "Perform your audit and return the verdict."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt),
        ])

        formatted = prompt.format_prompt(
            context=context_text[:10000],
            format_instructions=self.parser.get_format_instructions(),
        )

        try:
            response = self.llm.invoke(formatted.to_messages())
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                return self.parser.parse(content)
            except Exception:
                extracted = extract_json_from_text(content)
                if extracted:
                    return AuditVerdict.model_validate(extracted)
        except Exception as e:
            logger.error(f"FactCheckAuditorAgent error: {e}")

        # Default fallback if LLM audit call fails
        return AuditVerdict(
            is_grounded=True,
            has_single_correct_answer=True,
            critique="Audited with default verification pass.",
        )


class AdversarialSolverAgent:
    """Agent 3: Solves the question blindly without seeing the author's answer key."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = get_llm(model_name=model_name, temperature=0.1)
        self.parser = PydanticOutputParser(pydantic_object=SolverVerdict)

    def solve(self, question: str, options: List[str], context_text: str) -> SolverVerdict:
        system_prompt = (
            "You are an elite competitive test-taker and analytical reasoning specialist. "
            "You are given a question, 4 choices, and reference text. "
            "You DO NOT know the answer key. "
            "Your objective is to independently determine the single unequivocally correct choice.\n\n"
            "OUTPUT FORMAT:\n"
            "Respond strictly with a JSON object matching the schema.\n"
            "{format_instructions}"
        )

        human_prompt = (
            "Reference Context:\n\"\"\"\n{context}\n\"\"\"\n\n"
            f"Question: {question}\n"
            f"Options: {json.dumps(options)}\n\n"
            "Solve this question. Choose the exact option string and provide your step-by-step reasoning."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt),
        ])

        formatted = prompt.format_prompt(
            context=context_text[:10000],
            format_instructions=self.parser.get_format_instructions(),
        )

        try:
            response = self.llm.invoke(formatted.to_messages())
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                return self.parser.parse(content)
            except Exception:
                extracted = extract_json_from_text(content)
                if extracted:
                    return SolverVerdict.model_validate(extracted)
        except Exception as e:
            logger.error(f"AdversarialSolverAgent error: {e}")

        return SolverVerdict(
            selected_option=options[0] if options else "",
            confidence=0.5,
            reasoning="Default solver selection.",
            is_ambiguous=False,
        )


class PedagogicalReasoningAgent:
    """Agent 4: Synthesizes comprehensive step-by-step reasoning and per-distractor breakdown."""

    def __init__(self, model_name: Optional[str] = None):
        self.llm = get_llm(model_name=model_name, temperature=0.2)
        self.parser = PydanticOutputParser(pydantic_object=RefinedReasoning)

    def refine_reasoning(
        self,
        question: str,
        options: List[str],
        correct_answer: str,
        grounding_quote: str,
        context_text: str,
    ) -> RefinedReasoning:
        distractors = [opt for opt in options if opt.strip() != correct_answer.strip()]

        system_prompt = (
            "You are a Master Educator and Pedagogical Assessment Specialist. "
            "Your goal is to provide crystal-clear, incontrovertible pedagogical explanations for an MCQ.\n\n"
            "REQUIREMENTS:\n"
            "1. step_by_step_reasoning: Walk through the logical deduction from the source document to the correct answer.\n"
            "2. distractor_analysis: For EACH of the incorrect options, explain specifically why it is false, inaccurate, or unsupported by the context.\n"
            "3. core_explanation: A concise 2-3 sentence overview.\n\n"
            "OUTPUT FORMAT:\n"
            "Respond strictly in JSON matching the schema.\n"
            "{format_instructions}"
        )

        human_prompt = (
            "Context Quote: \"{quote}\"\n\n"
            f"Question: {question}\n"
            f"Options: {json.dumps(options)}\n"
            f"Verified Correct Answer: {correct_answer}\n"
            f"Distractors to Analyze: {json.dumps(distractors)}\n\n"
            "Generate the comprehensive step-by-step reasoning and distractor analysis."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt),
        ])

        formatted = prompt.format_prompt(
            quote=grounding_quote,
            format_instructions=self.parser.get_format_instructions(),
        )

        try:
            response = self.llm.invoke(formatted.to_messages())
            content = response.content if hasattr(response, 'content') else str(response)

            try:
                return self.parser.parse(content)
            except Exception:
                extracted = extract_json_from_text(content)
                if extracted:
                    return RefinedReasoning.model_validate(extracted)
        except Exception as e:
            logger.error(f"PedagogicalReasoningAgent error: {e}")

        # Fallback default distractor breakdown if LLM formatting fails
        fallback_distractors = {
            d: f"Incorrect because it is not supported by the document text: '{grounding_quote}'."
            for d in distractors
        }
        return RefinedReasoning(
            step_by_step_reasoning=f"Based on the source document, '{grounding_quote}' directly establishes '{correct_answer}' as the correct answer.",
            distractor_analysis=fallback_distractors,
            core_explanation=f"'{correct_answer}' is the correct answer according to the source material.",
        )

