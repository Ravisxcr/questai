"""
Multi-Agent MCQ Generation & Verification System
Guarantees 100% factual accuracy, source grounding, adversarial consensus, and deep reasoning.
"""

from .pipeline import run_mcq_multiagent_pipeline
from .schemas import VerifiedMCQ, CandidateMCQ, AuditVerdict, SolverVerdict

__all__ = [
    'run_mcq_multiagent_pipeline',
    'VerifiedMCQ',
    'CandidateMCQ',
    'AuditVerdict',
    'SolverVerdict',
]

