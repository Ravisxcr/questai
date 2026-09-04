# QuestAI: AI Study Arenas & Assessment Platform

A modular, privacy-first study and assessment platform inspired by **NotebookLM**. Organize course materials and documents into isolated **Arenas**, upload multiple PDFs, extract text and generate **Multiple Choice (MCQ)**, **Short Answer**, and **Long / Essay** questions via **LangChain** and **Ollama** in the background using **Celery**, take timed interactive quiz attempts, and analyze performance on the **Analytics Dashboard**.

---

## Key Features

- **NotebookLM-style Arenas**: Isolate unrelated PDFs into dedicated workspaces with custom color accents and descriptions. Full CRUD support.
- **Multi-PDF Ingestion**: Upload $N$ PDFs per Arena.
- **Background Processing with Celery & Redis**: Background text extraction and question generation so web requests never time out on large documents.
- **AI-Powered Question Generation (LangChain + Ollama)**:
  - **Multiple Choice Questions (MCQ)**: 4 distinct choices, single correct answer, and explanation.
  - **Short Answer Questions**: 1–3 sentence conceptual model answers with key concepts rubric.
  - **Long / Essay Questions**: Comprehensive sample answers and detailed grading rubrics.
  - **Structured Pydantic Schemas**: Guaranteed strict JSON parsing with markdown fallback repair.
- **Interactive Quiz Engine**:
  - Timed test taking with live stopwatch.
  - Instant auto-grading of MCQs.
  - Interactive self-assessment for short and long answers with live score adjustment via AJAX.
  - Persistent attempt history with duration and letter grades (A–F).
- **Analytics Dashboard**:
  - High-level KPIs: Total Arenas, PDFs, Questions, Attempts, Average Score %, and Total Study Time.
  - Interactive Chart.js charts: Accuracy progression timeline and question type breakdown.
  - Arena performance comparison table.
- **Exporting**: Export entire question banks to **Markdown** or **JSON** for Anki, Obsidian, or printing.

---

## Architecture Overview

```
questai/
├── manage.py                          # Django CLI entrypoint
├── questai/                           # Project root configuration
│   ├── celery.py                      # Celery app configuration
│   ├── settings.py                    # Django settings (Celery, SQLite, Ollama, static/media)
│   └── urls.py                        # Root URL routing
├── apps/
│   ├── arenas/                        # Arenas & PDF documents module
│   │   ├── models.py                  # Arena & Document models
│   │   ├── forms.py                   # Arena & Multi-PDF upload forms
│   │   ├── views.py                   # Workspace view, upload, task polling API
│   │   └── templates/arenas/          # 3-panel NotebookLM-style workspace
│   ├── questions/                     # Question bank & Celery task tracking
│   │   ├── models.py                  # Question & GenerationTask models
│   │   ├── views.py                   # Export (JSON/MD) & deletion
│   │   └── templates/questions/
│   ├── quizzes/                       # Interactive test-taking & attempt history
│   │   ├── models.py                  # QuizAttempt & AttemptAnswer models
│   │   ├── views.py                   # Quiz taking, grading, self-rating API, history
│   │   └── templates/quizzes/
│   ├── analytics/                     # Analytics & insights
│   │   ├── views.py                   # Metric aggregations & Chart.js data
│   │   └── templates/analytics/       # Visual dashboard
│   └── services/                      # Background processing & AI layer
│       ├── pdf_extractor.py           # pypdf text extraction & chunking
│       ├── schemas.py                 # Pydantic schemas for questions
│       ├── ollama_client.py           # Ollama healthcheck & model listing
│       ├── langchain_generator.py     # LangChain ChatOllama chains
│       └── tasks.py                   # Celery tasks for async processing
└── tests/                             # Full automated test suite (13 tests)
```

---

## Getting Started

### 1. Prerequisites
- **Python**: 3.12+
- **Ollama**: Installed locally ([ollama.ai](https://ollama.com)) with a model pulled:
  ```bash
  ollama pull llama3.2
  ```
- **Redis** (optional for Celery async worker):
  ```bash
  sudo service redis-server start
  ```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

---

## Service Management with Taskfile

A `Taskfile.yml` is provided to simplify service startup, background management, monitoring, and teardown:

| Command | Description |
|---|---|
| `task up` | Start Redis, Celery worker, and Django server in background |
| `task down` | Gracefully tear down all background services |
| `task restart` | Restart all background services |
| `task status` | Check live status of Redis, Celery, Django, and Ollama |
| `task server` | Run Django development server in foreground |
| `task worker` | Run Celery worker in foreground |
| `task logs:all` | Tail combined logs for Django and Celery |
| `task test` | Run automated test suite (13 unit & integration tests) |
| `task seed` | Seed demo Arena with sample questions and attempt |
| `task clean` | Clean up temporary files, cache, and logs |

---

### Manual Execution (Without Task)

#### 1. Database Migrations
```bash
python manage.py migrate
```

#### 2. Optional: Seed Demo Data
```bash
python manage.py seed_demo
```

#### 3. Running Services
##### Terminal 1: Celery Worker
```bash
celery -A questai worker -l info
```

##### Terminal 2: Django Server
```bash
python manage.py runserver 0.0.0.0:8000
```

Open your browser at [http://localhost:8000](http://localhost:8000).

---

## Running Tests
Run the comprehensive automated test suite:
```bash
python manage.py test tests
```
All 13 tests verify Arena isolation, PDF text extraction, LangChain schemas, quiz scoring, and analytics metrics.

