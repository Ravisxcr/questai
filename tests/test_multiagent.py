from unittest.mock import MagicMock, patch
from django.test import TestCase
from apps.arenas.models import Arena
from apps.questions.models import Question
from apps.services.multiagent.schemas import (
    CandidateMCQ,
    AuditVerdict,
    SolverVerdict,
    RefinedReasoning,
    VerifiedMCQ,
)
from apps.services.multiagent.pipeline import (
    normalize_choice,
    options_match,
    run_mcq_multiagent_pipeline,
)


class MultiAgentMCQTests(TestCase):
    def setUp(self):
        self.arena = Arena.objects.create(
            name="Operating Systems Arena",
            description="Process management and memory hierarchy",
            color_theme="indigo"
        )
        self.sample_context = (
            "Virtual memory is a memory management capability of an operating system "
            "that uses hardware and software to allow a computer to compensate for "
            "physical memory shortages by temporarily transferring data from random access "
            "memory (RAM) to disk storage. Paging is a memory management scheme by which "
            "a computer stores and retrieves data from secondary storage for use in main memory."
        )

    def test_schema_instantiation_and_validation(self):
        """Verify schema typing and field integrity."""
        candidate = CandidateMCQ(
            question="What does virtual memory use to compensate for physical RAM shortages?",
            options=["Disk storage", "CPU Cache", "Network bandwidth", "GPU VRAM"],
            designated_answer="Disk storage",
            source_quote="temporarily transferring data from random access memory (RAM) to disk storage.",
            difficulty="EASY"
        )
        self.assertEqual(candidate.designated_answer, "Disk storage")
        self.assertEqual(len(candidate.options), 4)

        audit = AuditVerdict(
            is_grounded=True,
            has_single_correct_answer=True,
            critique="The question is 100% grounded in the text."
        )
        self.assertTrue(audit.is_grounded)
        self.assertTrue(audit.has_single_correct_answer)

        solver = SolverVerdict(
            selected_option="Disk storage",
            confidence=0.98,
            reasoning="The passage explicitly states data is transferred to disk storage.",
            is_ambiguous=False
        )
        self.assertEqual(solver.selected_option, "Disk storage")

        refined = RefinedReasoning(
            step_by_step_reasoning="Step 1: The document defines virtual memory.\nStep 2: It mentions data transfer to disk storage.",
            distractor_analysis={
                "CPU Cache": "Not mentioned as secondary storage for virtual memory.",
                "Network bandwidth": "Pertains to networking, not host virtual memory.",
                "GPU VRAM": "Used for graphical rendering."
            },
            core_explanation="Virtual memory transfers data from RAM to disk storage."
        )
        self.assertIn("CPU Cache", refined.distractor_analysis)

    def test_option_matching_helpers(self):
        """Test normalization and matching across variations (e.g. 'A) London' vs 'London')."""
        self.assertEqual(normalize_choice("A) London"), "london")
        self.assertEqual(normalize_choice("London"), "london")
        self.assertTrue(options_match("A) London", "London"))
        self.assertTrue(options_match("Paris", "B) Paris"))
        self.assertFalse(options_match("London", "Paris"))

    @patch("apps.services.multiagent.pipeline.ItemWriterAgent")
    @patch("apps.services.multiagent.pipeline.FactCheckAuditorAgent")
    @patch("apps.services.multiagent.pipeline.AdversarialSolverAgent")
    @patch("apps.services.multiagent.pipeline.PedagogicalReasoningAgent")
    def test_multiagent_pipeline_success(self, MockRefiner, MockSolver, MockAuditor, MockWriter):
        """Test complete 4-agent consensus pipeline producing verified MCQs."""
        # 1. Mock Writer
        mock_writer_inst = MagicMock()
        mock_writer_inst.draft.return_value = [
            CandidateMCQ(
                question="What does virtual memory use to compensate for physical RAM shortages?",
                options=["Disk storage", "CPU Cache", "Network bandwidth", "GPU VRAM"],
                designated_answer="Disk storage",
                source_quote="temporarily transferring data from random access memory (RAM) to disk storage.",
                difficulty="MEDIUM"
            )
        ]
        MockWriter.return_value = mock_writer_inst

        # 2. Mock Auditor (Pass)
        mock_auditor_inst = MagicMock()
        mock_auditor_inst.audit.return_value = AuditVerdict(
            is_grounded=True,
            has_single_correct_answer=True,
            critique="Fully grounded in source text."
        )
        MockAuditor.return_value = mock_auditor_inst

        # 3. Mock Solver (Consensus match!)
        mock_solver_inst = MagicMock()
        mock_solver_inst.solve.return_value = SolverVerdict(
            selected_option="Disk storage",
            confidence=0.95,
            reasoning="Directly supported by the document definition of virtual memory.",
            is_ambiguous=False
        )
        MockSolver.return_value = mock_solver_inst

        # 4. Mock Refiner (Deep reasoning & distractor analysis)
        mock_refiner_inst = MagicMock()
        mock_refiner_inst.refine_reasoning.return_value = RefinedReasoning(
            step_by_step_reasoning="1. Document notes physical memory shortages.\n2. Discloses disk storage as the backing transfer target.",
            distractor_analysis={
                "CPU Cache": "CPU cache is ultra-fast on-die memory, not secondary backing storage.",
                "Network bandwidth": "Applies to packet transmission, not OS virtual memory.",
                "GPU VRAM": "Applies to dedicated graphics processing units."
            },
            core_explanation="Disk storage serves as the backing store for virtual memory pages."
        )
        MockRefiner.return_value = mock_refiner_inst

        # Run pipeline
        results = run_mcq_multiagent_pipeline(
            context_text=self.sample_context,
            count=1,
            difficulty="MEDIUM"
        )

        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item.question, "What does virtual memory use to compensate for physical RAM shortages?")
        self.assertEqual(item.correct_answer, "Disk storage")
        self.assertIn("CPU Cache", item.distractor_analysis)
        self.assertIn("physical memory shortages", item.step_by_step_reasoning)
        self.assertEqual(item.grounding_evidence, "temporarily transferring data from random access memory (RAM) to disk storage.")

    @patch("apps.services.multiagent.pipeline.ItemWriterAgent")
    @patch("apps.services.multiagent.pipeline.FactCheckAuditorAgent")
    @patch("apps.services.multiagent.pipeline.AdversarialSolverAgent")
    @patch("apps.services.multiagent.pipeline.PedagogicalReasoningAgent")
    def test_multiagent_pipeline_rejects_hallucination_or_ambiguity(self, MockRefiner, MockSolver, MockAuditor, MockWriter):
        """Test that questions failing audit or solver consensus are rejected."""
        mock_writer_inst = MagicMock()
        mock_writer_inst.draft.return_value = [
            CandidateMCQ(
                question="Candidate with hallucination",
                options=["A", "B", "C", "D"],
                designated_answer="A",
                source_quote="None",
            )
        ]
        MockWriter.return_value = mock_writer_inst

        # Auditor rejects
        mock_auditor_inst = MagicMock()
        mock_auditor_inst.audit.return_value = AuditVerdict(
            is_grounded=False,
            has_single_correct_answer=False,
            critique="Hallucination not in source text."
        )
        MockAuditor.return_value = mock_auditor_inst

        results = run_mcq_multiagent_pipeline(
            context_text=self.sample_context,
            count=1,
        )

        self.assertEqual(len(results), 0)

    def test_question_model_persistence(self):
        """Verify Question model persists multi-agent reasoning and distractor analysis."""
        q = Question.objects.create(
            arena=self.arena,
            question_type="MCQ",
            question_text="What is virtual memory?",
            options=["RAM to disk transfer", "CPU cache", "Network switch", "BIOS"],
            correct_answer="RAM to disk transfer",
            explanation="Transfers pages to disk.",
            step_by_step_reasoning="1. Check OS memory management.\n2. Deduce disk paging.",
            distractor_analysis={"CPU cache": "Fast SRAM", "Network switch": "Hardware device"},
            grounding_evidence="Temporarily transferring data to disk storage.",
            is_multiagent_verified=True,
        )

        q.refresh_from_db()
        self.assertTrue(q.is_multiagent_verified)
        self.assertEqual(q.distractor_analysis["CPU cache"], "Fast SRAM")
        self.assertIn("Check OS", q.step_by_step_reasoning)

