from django.test import TestCase
from django.utils import timezone
from apps.arenas.models import Arena, Document
from apps.questions.models import Question, GenerationTask
from apps.quizzes.models import QuizAttempt, AttemptAnswer


class ArenaAndQuestionModelTests(TestCase):
    def setUp(self):
        self.arena1 = Arena.objects.create(
            name="Distributed Systems",
            description="Consensus algorithms, Raft, Paxos",
            color_theme="indigo"
        )
        self.arena2 = Arena.objects.create(
            name="Cell Biology",
            description="Mitosis and meiosis",
            color_theme="emerald"
        )

    def test_arena_isolation(self):
        """Ensure documents and questions in one Arena are completely isolated from another."""
        # Create questions in arena 1
        q1 = Question.objects.create(
            arena=self.arena1,
            question_type="MCQ",
            question_text="What is the leader election timeout in Raft?",
            options=["150-300ms", "10-20s", "1-2s", "5-10ms"],
            correct_answer="150-300ms",
            explanation="Raft uses randomized election timeouts between 150ms and 300ms.",
        )
        
        # Create questions in arena 2
        q2 = Question.objects.create(
            arena=self.arena2,
            question_type="SHORT",
            question_text="Define apoptosis.",
            correct_answer="Programmed cell death.",
            explanation="Apoptosis is an orderly process where cell components are systematically dismantled.",
        )

        self.assertEqual(self.arena1.questions.count(), 1)
        self.assertEqual(self.arena2.questions.count(), 1)
        self.assertEqual(self.arena1.questions.first().question_text, q1.question_text)
        self.assertNotIn(q2, self.arena1.questions.all())

    def test_quiz_attempt_scoring_and_grades(self):
        """Test quiz attempt calculation and grade mapping."""
        q_mcq = Question.objects.create(
            arena=self.arena1,
            question_type="MCQ",
            question_text="What is Paxos?",
            options=["Consensus protocol", "Database engine", "Web browser", "OS kernel"],
            correct_answer="Consensus protocol",
        )

        attempt = QuizAttempt.objects.create(
            arena=self.arena1,
            title="Practice Quiz",
            total_questions=1,
            total_mcq_count=1,
            correct_mcq_count=1,
            score_percentage=100.0,
            duration_seconds=45,
            completed_at=timezone.now()
        )

        AttemptAnswer.objects.create(
            attempt=attempt,
            question=q_mcq,
            user_answer="Consensus protocol",
            is_correct=True,
        )

        self.assertEqual(attempt.grade, 'A')
        self.assertEqual(attempt.formatted_duration, "45s")
        self.assertEqual(self.arena1.average_score, 100.0)

    def test_generation_task_creation(self):
        """Verify generation task lifecycle tracking."""
        task = GenerationTask.objects.create(
            task_id="celery-uuid-1234",
            arena=self.arena1,
            status="PENDING",
            total_requested=6,
        )
        self.assertEqual(task.status, "PENDING")
        task.status = "SUCCESS"
        task.generated_count = 6
        task.save()
        self.assertEqual(task.generated_count, 6)

