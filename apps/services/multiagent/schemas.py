from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class CandidateMCQ(BaseModel):
    """Initial candidate drafted by the Item Writer Agent."""
    question: str = Field(description="The question text")
    options: List[str] = Field(description="Exactly 4 distinct choices")
    designated_answer: str = Field(description="The option designated as correct")
    source_quote: str = Field(description="Direct sentence or passage from the context that proves this answer")
    difficulty: str = Field(default="MEDIUM", description="EASY, MEDIUM, or HARD")


class CandidateBatch(BaseModel):
    """Container for drafted candidate questions."""
    candidates: List[CandidateMCQ] = Field(default_factory=list)


class AuditVerdict(BaseModel):
    """Output from the Fact-Checking Auditor Agent."""
    is_grounded: bool = Field(description="True if question and correct answer are 100% supported by the text without assumptions")
    has_single_correct_answer: bool = Field(description="True if there is unambiguously only 1 correct choice among the 4")
    critique: str = Field(description="Detailed critique of grounding, clarity, and option plausibility")
    suggested_fix: Optional[str] = Field(default=None, description="Suggested wording adjustments if revision is needed")


class SolverVerdict(BaseModel):
    """Output from the Blind Adversarial Solver Agent."""
    selected_option: str = Field(description="The option chosen by the solver based on logical deduction")
    confidence: float = Field(default=1.0, description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Step-by-step reasoning that led to choosing this option")
    is_ambiguous: bool = Field(default=False, description="True if multiple options could be argued as correct or if question is unclear")


class RefinedReasoning(BaseModel):
    """Output from the Reasoning & Distractor Refiner Agent."""
    step_by_step_reasoning: str = Field(description="Comprehensive step-by-step deduction showing why the correct answer is true")
    distractor_analysis: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping each incorrect option to an explanation of why it is wrong/invalid"
    )
    core_explanation: str = Field(description="Clear summary explanation of the concept")


class VerifiedMCQ(BaseModel):
    """Final, verified Multiple Choice Question with guaranteed accuracy and complete reasoning."""
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    step_by_step_reasoning: str
    distractor_analysis: Dict[str, str]
    grounding_evidence: str
    difficulty: str = "MEDIUM"

