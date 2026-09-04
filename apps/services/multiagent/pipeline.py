import logging
from typing import List, Optional, Callable
from .schemas import VerifiedMCQ, CandidateMCQ
from .agents import (
    ItemWriterAgent,
    FactCheckAuditorAgent,
    AdversarialSolverAgent,
    PedagogicalReasoningAgent,
)

logger = logging.getLogger(__name__)


def normalize_choice(text: str) -> str:
    """Normalize choice text for comparison (e.g. 'A) London' vs 'London')."""
    if not text:
        return ""
    t = text.strip().lower()
    if len(t) > 3 and t[1:3] == ") ":
        t = t[3:].strip()
    return t


def options_match(opt1: str, opt2: str) -> bool:
    """Check if two option strings refer to the same choice."""
    n1 = normalize_choice(opt1)
    n2 = normalize_choice(opt2)
    return n1 == n2 or n1 in n2 or n2 in n1


def run_mcq_multiagent_pipeline(
    context_text: str,
    count: int = 3,
    difficulty: str = "MEDIUM",
    model_name: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> List[VerifiedMCQ]:
    """
    Executes the 4-agent consensus verification pipeline for MCQs:
    1. ItemWriterAgent: drafts candidate questions grounded in the text.
    2. FactCheckAuditorAgent: validates 100% factual grounding against the text.
    3. AdversarialSolverAgent: tests for unambiguous single-choice consensus.
    4. PedagogicalReasoningAgent: formulates step-by-step reasoning and distractor analysis.
    """
    if not context_text or count <= 0:
        return []

    writer = ItemWriterAgent(model_name=model_name)
    auditor = FactCheckAuditorAgent(model_name=model_name)
    solver = AdversarialSolverAgent(model_name=model_name)
    refiner = PedagogicalReasoningAgent(model_name=model_name)

    def notify(msg: str):
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass
        logger.info(msg)

    # Step 1: Draft candidate questions (ask for slight buffer to ensure target count)
    draft_request_count = count + 1 if count < 10 else count
    notify(f"Agent 1 (Item Writer): Drafting {draft_request_count} candidate MCQs from context...")
    
    candidates = writer.draft(context_text, count=draft_request_count, difficulty=difficulty)
    if not candidates:
        logger.warning("Drafting agent returned no candidates.")
        return []

    verified_mcqs: List[VerifiedMCQ] = []

    # Step 2: Verification Loop for each candidate
    for idx, cand in enumerate(candidates, 1):
        if len(verified_mcqs) >= count:
            break

        notify(f"Agent 2 & 3: Auditing & Adversarial Solving Question {idx}/{len(candidates)}...")

        # Agent 2: Grounding Audit
        audit = auditor.audit(cand, context_text)
        if not audit.is_grounded or not audit.has_single_correct_answer:
            logger.info(f"Question {idx} failed audit: {audit.critique}")
            continue

        # Agent 3: Blind Adversarial Solver
        solution = solver.solve(cand.question, cand.options, context_text)
        
        # Check consensus between Writer and Solver
        concordant = options_match(solution.selected_option, cand.designated_answer)
        if not concordant and not solution.is_ambiguous:
            logger.info(
                f"Question {idx} discordance: Writer='{cand.designated_answer}', Solver='{solution.selected_option}'"
            )
            continue

        # Step 4: Reasoning & Distractor Analysis Refiner
        notify(f"Agent 4: Synthesizing deep step-by-step reasoning for Question {idx}...")
        reasoning = refiner.refine_reasoning(
            question=cand.question,
            options=cand.options,
            correct_answer=cand.designated_answer,
            grounding_quote=cand.source_quote,
            context_text=context_text,
        )

        verified = VerifiedMCQ(
            question=cand.question,
            options=cand.options,
            correct_answer=cand.designated_answer,
            explanation=reasoning.core_explanation,
            step_by_step_reasoning=reasoning.step_by_step_reasoning,
            distractor_analysis=reasoning.distractor_analysis,
            grounding_evidence=cand.source_quote,
            difficulty=cand.difficulty or difficulty,
        )
        verified_mcqs.append(verified)

    notify(f"Multi-Agent Pipeline completed: {len(verified_mcqs)} questions verified.")
    return verified_mcqs

