from django.test import TestCase
from apps.services.schemas import QuestionBatchSchema, MCQItem, ShortAnswerItem, LongAnswerItem
from apps.services.langchain_generator import extract_json_from_text


class ServicesUnitTests(TestCase):
    def test_schema_serialization_and_validation(self):
        batch = QuestionBatchSchema(
            title="Operating Systems",
            summary="Process scheduling and synchronization",
            mcqs=[
                MCQItem(
                    question="Which scheduling algorithm is non-preemptive?",
                    options=["FCFS", "Round Robin", "SRTF", "Multilevel Feedback Queue"],
                    correct_answer="FCFS",
                    explanation="First-Come, First-Served executes processes until completion without preemption.",
                    difficulty="EASY"
                )
            ],
            short_answers=[
                ShortAnswerItem(
                    question="What is a deadlock?",
                    ideal_answer="A situation where a set of processes are blocked because each is holding a resource and waiting for another.",
                    key_points=["Mutual exclusion", "Hold and wait", "Circular wait", "No preemption"],
                    explanation="Coffman conditions describe deadlocks.",
                    difficulty="MEDIUM"
                )
            ],
            long_answers=[
                LongAnswerItem(
                    question="Analyze the Banker's algorithm for deadlock avoidance.",
                    sample_answer="The Banker's algorithm tests for safety by simulating the allocation of predetermined maximum possible amounts of all resources...",
                    key_points=["Safe state determination", "Resource-allocation graph", "Available and Need vectors"],
                    explanation="Guarantees safe state transitions.",
                    difficulty="HARD"
                )
            ]
        )

        self.assertEqual(len(batch.mcqs), 1)
        self.assertEqual(len(batch.short_answers), 1)
        self.assertEqual(len(batch.long_answers), 1)
        self.assertEqual(batch.mcqs[0].correct_answer, "FCFS")

    def test_extract_json_from_markdown(self):
        markdown_text = """
Here is the question set you requested:
```json
{
  "title": "Database Normalization",
  "summary": "1NF, 2NF, 3NF, BCNF",
  "mcqs": [
    {
      "question": "What does 2NF eliminate?",
      "options": ["Partial dependency", "Transitive dependency", "Atomic violation", "Multi-valued dependency"],
      "correct_answer": "Partial dependency",
      "explanation": "2NF requires 1NF and no partial dependencies on candidate keys.",
      "difficulty": "MEDIUM"
    }
  ],
  "short_answers": [],
  "long_answers": []
}
```
I hope this helps!
        """
        extracted = extract_json_from_text(markdown_text)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted["title"], "Database Normalization")
        self.assertEqual(len(extracted["mcqs"]), 1)

