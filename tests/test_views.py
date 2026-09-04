import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.arenas.models import Arena
from apps.questions.models import Question
from apps.quizzes.models import QuizAttempt, AttemptAnswer


class ViewIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.arena = Arena.objects.create(
            name="Quantum Physics",
            description="Quantum entanglement and wave-particle duality",
            color_theme="purple"
        )
        self.q1 = Question.objects.create(
            arena=self.arena,
            question_type="MCQ",
            question_text="What phenomenon describes particles that remain connected so actions on one affect the other?",
            options=["Quantum Entanglement", "Superposition", "Wave Collapse", "Tunneling"],
            correct_answer="Quantum Entanglement",
            explanation="Quantum entanglement connects states of particles regardless of distance.",
        )
        self.q2 = Question.objects.create(
            arena=self.arena,
            question_type="SHORT",
            question_text="State Heisenberg's Uncertainty Principle.",
            correct_answer="You cannot simultaneously know both the position and momentum of a particle with absolute precision.",
            key_points=["Position", "Momentum", "Precision limit"],
        )

    def test_arena_list_and_detail(self):
        # Arena list view
        resp = self.client.get(reverse('arenas:list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Quantum Physics")

        # Arena detail view
        resp_detail = self.client.get(reverse('arenas:detail', kwargs={'pk': str(self.arena.id)}))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, "Quantum Entanglement")

    def test_arena_create_post(self):
        post_data = {
            'name': 'Organic Chemistry',
            'description': 'Reaction mechanisms',
            'color_theme': 'emerald'
        }
        resp = self.client.post(reverse('arenas:create'), data=post_data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Arena.objects.filter(name='Organic Chemistry').exists())

    def test_question_export_json_and_markdown(self):
        # JSON export
        resp_json = self.client.get(reverse('questions:export', kwargs={'arena_pk': str(self.arena.id), 'format': 'json'}))
        self.assertEqual(resp_json.status_code, 200)
        self.assertEqual(resp_json['Content-Type'], 'application/json')
        data = json.loads(resp_json.content)
        self.assertEqual(data['total_questions'], 2)

        # Markdown export
        resp_md = self.client.get(reverse('questions:export', kwargs={'arena_pk': str(self.arena.id), 'format': 'markdown'}))
        self.assertEqual(resp_md.status_code, 200)
        self.assertEqual(resp_md['Content-Type'], 'text/markdown')
        self.assertIn(b"Quantum Physics", resp_md.content)

    def test_quiz_flow(self):
        # 1. Start quiz
        start_resp = self.client.post(
            reverse('quizzes:start', kwargs={'arena_pk': str(self.arena.id)}),
            data={'filter_type': 'ALL', 'limit': '0'}
        )
        self.assertEqual(start_resp.status_code, 302)
        
        attempt = QuizAttempt.objects.first()
        self.assertIsNotNone(attempt)

        # 2. Take quiz view
        take_resp = self.client.get(reverse('quizzes:take', kwargs={'pk': str(attempt.id)}))
        self.assertEqual(take_resp.status_code, 200)

        # 3. Submit quiz
        submit_data = {
            'duration_seconds': '35',
            f'question_{self.q1.id}': 'Quantum Entanglement',
            f'question_{self.q2.id}': 'Position and momentum uncertainty principle',
        }
        submit_resp = self.client.post(
            reverse('quizzes:submit', kwargs={'pk': str(attempt.id)}),
            data=submit_data
        )
        self.assertEqual(submit_resp.status_code, 302)

        attempt.refresh_from_db()
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.correct_mcq_count, 1)
        self.assertEqual(attempt.score_percentage, 100.0)

        # 4. View result
        res_resp = self.client.get(reverse('quizzes:attempt_result', kwargs={'pk': str(attempt.id)}))
        self.assertEqual(res_resp.status_code, 200)
        self.assertContains(res_resp, "Quantum Entanglement")

        # 5. Interactive self grade API on short answer
        ans_short = attempt.answers.filter(question=self.q2).first()
        grade_resp = self.client.post(
            reverse('quizzes:self_grade', kwargs={'pk': str(attempt.id), 'answer_pk': str(ans_short.id)}),
            data=json.dumps({'is_correct': True, 'self_rating': 5}),
            content_type='application/json'
        )
        self.assertEqual(grade_resp.status_code, 200)
        grade_data = json.loads(grade_resp.content)
        self.assertTrue(grade_data['success'])

    def test_analytics_dashboard(self):
        resp = self.client.get(reverse('analytics:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Study Analytics")
        self.assertContains(resp, "Quantum Physics")

