# EduAgent

[English](README.md) · [简体中文](README.zh-CN.md)

**Turn any course PDF into an AI tutor that knows what you learned, what you missed, and what to do next.**

Most PDF chatbots stop after answering a question. EduAgent turns course material into a continuous learning loop: it grounds explanations in your own lecture notes, shows the exact page behind an answer, generates targeted practice, identifies missing ideas and misconceptions, and keeps a lightweight learner profile so the next activity is more useful than the last one.

Upload a lecture. Ask a question. Practice one concept. Get feedback. Come back to your weak points. EduAgent is designed to make studying feel less like searching through slides and more like working with a patient tutor who remembers where you need help.

## Why EduAgent?

```text
Your course PDF
      ↓
Page-aware course knowledge base
      ↓
Grounded explanation with file + page citations
      ↓
Concept-focused quiz
      ↓
Formative feedback on missing points and misconceptions
      ↓
Learner profile and next teaching action
```

The core experience is simple:

**Understand → Practice → Receive feedback → Adjust the next step**

## What you can do

- **Ask questions about your own course** instead of searching through disconnected general answers.
- **Inspect the evidence** behind an answer with the source file and page number.
- **Get the right retrieval path for the question:** broad document questions use
  structure-aware overview context distributed across the PDF, while focused questions use
  the configured Top-K retrieval.
- **Change the explanation level** between Beginner, Standard, and Advanced.
- **Generate targeted practice** as multiple-choice or short-answer questions.
- **See why an answer needs improvement** through missing key points and possible misconceptions.
- **Track progress over time** with concept mastery, weak-concept detection, attempts, and scores.
- **Use a transparent teaching loop** that can choose explanation, example, remediation, or a harder quiz as the next action.

## Current status: the MVP is complete and ready to run locally

The core MVP is implemented and tested. It covers the complete path from course-material ingestion to learning-progress review:

- Page-aware PDF parsing, chunking, and duplicate detection
- Course-grounded retrieval with page citations
- Grounded Q&A with structured model output
- Multiple-choice and short-answer quiz generation
- Formative answer evaluation
- Learner profile, mastery heuristics, and weak-concept tracking
- Adaptive teaching policy
- Streamlit pages for Learn, Course Materials, Practice, Progress, and About
- Independent chat-model and embedding-provider configuration

“MVP complete” means the software loop is available for local use. It does not mean that the app is already a hosted multi-user product or that educational learning gains have been scientifically established. The current release is a single-student local MVP without authentication, OCR for scanned PDFs, or validated knowledge tracing.

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/Magician026/EduAgent.git
cd EduAgent
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
uv pip install -e .
```

Python 3.11+ is supported. If you do not use `uv`, create a regular virtual environment and install the same requirement files.

### 2. Configure two independent model services

EduAgent uses one service for chat generation and another service for embeddings. They may be the same provider, but they do not have to be. This is what lets you use DeepSeek or Kimi for tutoring while using a separate embedding service for PDF indexing and retrieval.

Copy the template:

```bash
cp .env.example .env
```

The provider-neutral configuration is:

```env
# Chat / tutoring model
EDUAGENT_LLM_API_KEY=your-chat-api-key
EDUAGENT_LLM_BASE_URL=https://your-chat-provider.example.com/v1
EDUAGENT_LLM_MODEL=your-chat-model

# Embedding model used for PDF indexing and query retrieval
EDUAGENT_EMBEDDING_API_KEY=your-embedding-api-key
EDUAGENT_EMBEDDING_BASE_URL=https://your-embedding-provider.example.com/v1
EDUAGENT_EMBEDDING_MODEL=your-embedding-model
```

The chat and embedding services must expose the OpenAI-compatible operations used by the app: Chat Completions for tutoring and `/embeddings` for indexing/retrieval.

### Provider presets

#### OpenAI for chat and embeddings

```env
EDUAGENT_LLM_API_KEY=sk-your-openai-key
EDUAGENT_LLM_BASE_URL=https://api.openai.com/v1
EDUAGENT_LLM_MODEL=gpt-4o-mini

EDUAGENT_EMBEDDING_API_KEY=sk-your-openai-key
EDUAGENT_EMBEDDING_BASE_URL=https://api.openai.com/v1
EDUAGENT_EMBEDDING_MODEL=text-embedding-3-small
```

#### DeepSeek for tutoring + OpenAI for embeddings

DeepSeek provides an OpenAI-compatible Chat Completions API. Its current official examples use `https://api.deepseek.com` with models such as `deepseek-v4-flash` and `deepseek-v4-pro`; see the [DeepSeek API documentation](https://api-docs.deepseek.com/) for current model availability.

```env
EDUAGENT_LLM_API_KEY=your-deepseek-api-key
EDUAGENT_LLM_BASE_URL=https://api.deepseek.com
EDUAGENT_LLM_MODEL=deepseek-v4-flash

EDUAGENT_EMBEDDING_API_KEY=sk-your-openai-key
EDUAGENT_EMBEDDING_BASE_URL=https://api.openai.com/v1
EDUAGENT_EMBEDDING_MODEL=text-embedding-3-small
```

#### Kimi / Moonshot for tutoring + OpenAI for embeddings

Kimi provides an OpenAI-compatible Chat Completions API. The current official endpoint is `https://api.moonshot.ai/v1`; the China endpoint `https://api.moonshot.cn/v1` is also documented by Moonshot. A current model example is `kimi-k2.6`; see the [Kimi API overview](https://platform.kimi.ai/docs/api/overview) and [model list](https://platform.kimi.ai/docs/models).

```env
EDUAGENT_LLM_API_KEY=your-moonshot-api-key
EDUAGENT_LLM_BASE_URL=https://api.moonshot.ai/v1
EDUAGENT_LLM_MODEL=kimi-k2.6

EDUAGENT_EMBEDDING_API_KEY=sk-your-openai-key
EDUAGENT_EMBEDDING_BASE_URL=https://api.openai.com/v1
EDUAGENT_EMBEDDING_MODEL=text-embedding-3-small
```

#### Any other OpenAI-compatible provider

You can use another provider or gateway by setting its chat endpoint and model in `EDUAGENT_LLM_*`, and an embedding-capable endpoint and model in `EDUAGENT_EMBEDDING_*`.

For backward compatibility, the legacy `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, and `OPENAI_EMBEDDING_MODEL` variables are still accepted for a single-provider setup.

### 3. Start the app

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

### 4. Your first learning session

1. Open **Course Materials** and upload a lecture PDF.
2. Click **Index selected PDFs** and wait for indexing to finish.
3. Open **Learn** and ask a specific question about the lecture.
4. Expand the source card and check the cited file and page.
5. Open **Practice**, choose the concept, and generate a quiz.
6. Submit your answer and read the missing points or misconception feedback.
7. Open **Progress** to review mastery, weak concepts, and recent attempts.

## What happens without an API key?

The UI still starts and shows configuration guidance and the About page. The repository also includes an offline technical smoke evaluation that does not call a model provider:

```bash
python examples/create_sample_pdf.py
PYTHONPATH=src python -m eduagent.evaluation.rag_evaluator \
  --dataset examples/evaluation_dataset.json
```

This checks document parsing, source retrieval, and latency on self-authored sample content. It is not a production-quality benchmark and does not claim educational impact.

## What is next?

### Try it with one real course

Configure the two services, upload one course, and complete the full loop: **question → citation → quiz → feedback → progress**. Pay special attention to citation accuracy, question relevance, and whether the feedback changes what you study next.

### Turn the MVP into a stable product

- Multi-user authentication, data isolation, and durable storage
- Multi-course management with chapters and concept relationships
- OCR for scanned lecture materials
- Better retrieval, question quality, model routing, and cost controls
- A deployment environment with explicit privacy and retention policies

### Verify learning impact

Retrieval metrics tell us whether the system found relevant material; they do not prove that a learner learned more. A future study should use pre-tests, post-tests, and a suitable comparison condition to evaluate learning outcomes separately from engineering quality.

## Technical overview

The app uses Streamlit for the interface, PyMuPDF for page-level PDF parsing, Chroma for local vector storage, SQLite for learner profiles and activity, an OpenAI-compatible chat adapter for explanations/quizzes/feedback, and an independent OpenAI-compatible embedding adapter for indexing and retrieval. The next-action policy is deterministic and interpretable; the model generates the educational language and structured feedback.

Runtime data is stored under `data/runtime/` and ignored by Git. The current MVP is intended for local single-student use; do not upload sensitive or restricted course materials without reviewing privacy, retention, and access requirements.

## Documentation

- [Product demo](docs/demo.md)
- [Architecture](docs/architecture.md)
- [Technical evaluation and future impact study](docs/impact_study.md)

## Known limitations

- Single-student local MVP; no authentication or multi-user isolation
- Local Chroma and SQLite persistence; hosted filesystem durability is not guaranteed
- No OCR for scanned PDFs
- Automated evaluation is formative feedback, not official grading
- Mastery is a transparent heuristic, not validated knowledge tracing
- Answer quality depends on course text quality, retrieval, provider compatibility, and model configuration
- Page citations point to supporting evidence; this MVP does not replace reading the source
  material or expert judgment.

## License

This project does not currently declare a separate open-source license. Add a license and review third-party dependency terms before public distribution or commercial use.
