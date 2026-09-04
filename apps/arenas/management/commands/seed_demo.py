from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.arenas.models import Arena, Document
from apps.questions.models import Question
from apps.quizzes.models import QuizAttempt, AttemptAnswer


class Command(BaseCommand):
    help = "Seed demo Arena, sample questions, and quiz attempts for immediate testing."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        arena, _ = Arena.objects.get_or_create(
            name="Computer Networking & Distributed Systems",
            defaults={
                "description": "TCP/IP architecture, consensus protocols, DNS resolution, and latency optimization.",
                "color_theme": "indigo",
            }
        )

        # Create demo questions
        questions_data = [
            {
                "question_type": "MCQ",
                "difficulty": "MEDIUM",
                "question_text": "In the TCP 3-way handshake, what is the sequence of flag packets sent between client and server?",
                "options": ["SYN -> SYN-ACK -> ACK", "ACK -> SYN -> SYN-ACK", "SYN -> ACK -> FIN", "HELLO -> ACK -> DATA"],
                "correct_answer": "SYN -> SYN-ACK -> ACK",
                "explanation": "The client sends a SYN packet, the server responds with SYN-ACK, and the client confirms with ACK to establish a reliable full-duplex connection.",
                "key_points": ["SYN flag", "SYN-ACK response", "ACK final confirmation"],
            },
            {
                "question_type": "MCQ",
                "difficulty": "HARD",
                "question_text": "Which property does the Raft consensus algorithm guarantee in distributed state machines?",
                "options": ["Leader Completeness", "Byzantine Fault Tolerance", "Infinite Scalability", "Zero Network Overhead"],
                "correct_answer": "Leader Completeness",
                "explanation": "If a log entry is committed in a given term, then that entry will be present in the logs of the leaders for all higher-numbered terms.",
                "key_points": ["Leader completeness", "Safety invariant", "Log replication"],
            },
            {
                "question_type": "SHORT",
                "difficulty": "MEDIUM",
                "question_text": "Explain the key difference between TCP and UDP transport protocols.",
                "options": [],
                "correct_answer": "TCP is a connection-oriented protocol providing guaranteed in-order delivery, flow control, and error correction. UDP is connectionless and best-effort, offering lower latency with no delivery guarantees.",
                "explanation": "TCP sacrifices latency for reliability and ordered byte-stream delivery, whereas UDP prioritizes minimal latency for applications like real-time audio/video.",
                "key_points": ["Connection-oriented vs Connectionless", "Reliability and packet ordering", "Overhead and latency trade-offs"],
            },
            {
                "question_type": "LONG",
                "difficulty": "HARD",
                "question_text": "Analyze how DNS resolution works from a user entering a URL to the browser establishing a TCP connection. Describe each tier of DNS servers involved.",
                "options": [],
                "correct_answer": "1. The browser checks local cache, then OS cache.\n2. The query is forwarded to the Recursive Resolver (ISP/public DNS).\n3. The resolver queries the Root DNS Server (which directs to TLD server).\n4. The resolver queries the Top-Level Domain (TLD) server (e.g. .com, .org).\n5. The resolver queries the Authoritative Name Server, which returns the actual IP record (A/AAAA).\n6. The resolver caches the result and returns the IP to the client, which initiates the TCP handshake.",
                "explanation": "DNS is a hierarchical, distributed database designed to provide scalable hostname-to-IP resolution with multiple caching levels.",
                "key_points": ["Root servers", "TLD servers", "Authoritative name servers", "Recursive resolvers and caching"],
            },
        ]

        for q_data in questions_data:
            Question.objects.get_or_create(
                arena=arena,
                question_text=q_data["question_text"],
                defaults=q_data
            )

        # Create a sample completed attempt
        if not arena.attempts.exists():
            attempt = QuizAttempt.objects.create(
                arena=arena,
                title="Networking Practice Test",
                question_filter="ALL",
                total_questions=4,
                total_mcq_count=2,
                correct_mcq_count=2,
                score_percentage=100.0,
                duration_seconds=115,
                completed_at=timezone.now(),
            )
            for q in arena.questions.all():
                AttemptAnswer.objects.create(
                    attempt=attempt,
                    question=q,
                    user_answer=q.correct_answer,
                    is_correct=True,
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded demo Arena: {arena.name} with {arena.questions.count()} questions and a sample quiz attempt."))

