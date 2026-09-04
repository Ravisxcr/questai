from typing import List, Optional
from pydantic import BaseModel, Field


class MCQItem(BaseModel):
    """Schema for a Multiple Choice Question."""
    question: str = Field(description="The question prompt")
    options: List[str] = Field(description="List of exactly 4 distinct answer choices")
    correct_answer: str = Field(description="The exact text of the correct option")
    explanation: str = Field(description="Detailed explanation of why this choice is correct and others are incorrect")
    difficulty: str = Field(default="MEDIUM", description="EASY, MEDIUM, or HARD")


class ShortAnswerItem(BaseModel):
    """Schema for a Short Answer / Conceptual Question."""
    question: str = Field(description="The conceptual or factual question")
    ideal_answer: str = Field(description="Concise 1-3 sentence model answer")
    key_points: List[str] = Field(default_factory=list, description="List of essential keywords or concepts required for a complete answer")
    explanation: str = Field(description="Context and deeper explanation")
    difficulty: str = Field(default="MEDIUM", description="EASY, MEDIUM, or HARD")


class LongAnswerItem(BaseModel):
    """Schema for a Long / Analytical / Essay Question."""
    question: str = Field(description="In-depth, analytical, or scenario-based question")
    sample_answer: str = Field(description="Comprehensive, well-structured sample answer")
    key_points: List[str] = Field(default_factory=list, description="Grading rubric points and criteria")
    explanation: str = Field(description="Key concepts and pedagogical explanation")
    difficulty: str = Field(default="HARD", description="EASY, MEDIUM, or HARD")


class QuestionBatchSchema(BaseModel):
    """Batch container for all generated question types."""
    title: Optional[str] = Field(default="Generated Q&A Set", description="A descriptive title for this set of questions")
    summary: Optional[str] = Field(default="", description="A short 1-2 sentence overview of the covered content")
    mcqs: List[MCQItem] = Field(default_factory=list, description="Generated MCQs")
    short_answers: List[ShortAnswerItem] = Field(default_factory=list, description="Generated short answer questions")
    long_answers: List[LongAnswerItem] = Field(default_factory=list, description="Generated long answer questions")

