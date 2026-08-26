# EduAgent P0 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a deployable Streamlit MVP that ingests course PDFs, answers with citations, generates and evaluates quizzes, updates a transparent learner profile, and chooses the next teaching action.

**Architecture:** A single Streamlit process composes page renderers with an application service container. PyMuPDF produces page-aware chunks, an OpenAI-compatible adapter produces embeddings and structured LLM output, Chroma persists local vectors, and SQLite persists the single-student profile and activity. The application, not the LLM, owns the deterministic teaching policy.

**Tech Stack:** Python 3.12, Streamlit, PyMuPDF, Chroma, OpenAI Python SDK, Pydantic, SQLite, NumPy, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-08-26-eduagent-mvp-design.md`

## Global Constraints

- Use Python 3.12 for local verification and document Python 3.11+ compatibility where dependencies permit.
- Use Streamlit as the only UI/runtime process; do not add React, a separate backend, queues, Redis, or authentication.
- Keep uploaded files, Chroma data, and SQLite runtime data under ignored `data/runtime/`.
- Load model credentials only from environment variables or Streamlit secrets; never hard-code or log them.
- Preserve `document_name`, `page`, `chunk_id`, and excerpt information through retrieval so citations are application-generated.
- Use Pydantic validation for quiz and answer-evaluation objects; malformed provider JSON gets at most one repair attempt.
- Treat LLM evaluation as automated formative feedback, not objective human grading.
- Use the deterministic mastery heuristic: first mastery equals score; later mastery is `0.70 * previous + 0.30 * score`; weak means mastery `< 0.60`.
- The teaching policy must be deterministic and covered by unit tests.
- Do not claim real deployment, student usage, accuracy, or learning gains unless actually verified or measured.
- End every task with a focused test command and a small Git commit.

## File Map

### Bootstrap and configuration

- Create `app.py`: Streamlit entry point, `src` bootstrap, cached service construction, page routing.
- Create `pyproject.toml`: package metadata, pytest configuration, Ruff configuration.
- Create `requirements.txt`: runtime dependencies for Streamlit Cloud.
- Create `requirements-dev.txt`: test and lint dependencies.
- Create `.env.example`: documented provider and runtime settings with empty secret values.
- Create `.gitignore`: protect `.env`, virtual environments, caches, and `data/runtime/`.
- Create `.streamlit/config.toml`: safe headless/theme defaults.
- Create `data/.gitkeep` and `data/runtime/.gitkeep`.
- Create `src/eduagent/__init__.py` and package `__init__.py` files.

### Domain and document processing

- Create `src/eduagent/models.py`: enums and Pydantic domain contracts.
- Create `src/eduagent/config.py`: environment/secret-aware immutable settings.
- Create `src/eduagent/document_processing/parser.py`: PDF-to-page extraction.
- Create `src/eduagent/document_processing/chunker.py`: deterministic page-aware chunking.
- Create `src/eduagent/document_processing/ingestion.py`: hashing, duplicate detection, parsing, embedding, vector insertion, and document registration.

### Retrieval and provider layer

- Create `src/eduagent/llm/provider.py`: provider protocol, OpenAI-compatible implementation, safe errors, JSON validation, and bounded repair.
- Create `src/eduagent/retrieval/embeddings.py`: embedding protocol and provider-backed adapter.
- Create `src/eduagent/retrieval/vector_store.py`: Chroma adapter with metadata-preserving search.
- Create `src/eduagent/retrieval/retriever.py`: query embedding, top-k retrieval, source conversion, and context formatting.

### Student model and tutoring

- Create `src/eduagent/student/profile.py`: pure mastery and weak-concept functions.
- Create `src/eduagent/student/repository.py`: SQLite schema and parameterized persistence methods.
- Create `src/eduagent/tutor/teaching_policy.py`: deterministic teaching-action selection.
- Create `src/eduagent/tutor/quiz_generator.py`: grounded quiz prompt and validated generation.
- Create `src/eduagent/tutor/answer_evaluator.py`: formative evaluation prompt and validation.
- Create `src/eduagent/tutor/tutor_agent.py`: retrieval/provider/policy composition.

### UI, evaluation, and portfolio materials

- Create `src/eduagent/ui/pages.py`: focused Streamlit page renderers and reusable UI helpers.
- Create `src/eduagent/evaluation/rag_evaluator.py`: JSON dataset evaluator and CLI entry point.
- Create `examples/sample_course.md`: self-authored course content source.
- Create `examples/create_sample_pdf.py`: deterministic script for generating `examples/sample_course.pdf` with PyMuPDF.
- Create `examples/evaluation_dataset.json`: small source-aware retrieval dataset.
- Create `docs/architecture.md`, `docs/demo.md`, `docs/impact_study.md`, and `docs/cv_material.md`.
- Create `README.md`: portfolio overview, setup, deployment, evaluation honesty, and screenshot checklist.

### Tests

- Create `tests/conftest.py`: temporary settings, SQLite paths, and fake providers.
- Create `tests/test_config.py`.
- Create `tests/test_models.py`.
- Create `tests/test_parser.py`.
- Create `tests/test_chunker.py`.
- Create `tests/test_ingestion.py`.
- Create `tests/test_retrieval.py`.
- Create `tests/test_profile.py`.
- Create `tests/test_repository.py`.
- Create `tests/test_teaching_policy.py`.
- Create `tests/test_tutor.py`.

---

### Task 1: Bootstrap a runnable, testable Python package

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `.streamlit/config.toml`
- Create: `data/.gitkeep`
- Create: `data/runtime/.gitkeep`
- Create: `src/eduagent/__init__.py`
- Create: package `__init__.py` files under `src/eduagent/`
- Create: `app.py`
- Test: `tests/conftest.py`, `tests/test_config.py`

**Interfaces:**
- Produces `Settings.from_sources(env: Mapping[str, str] | None = None, secrets: Mapping[str, Any] | None = None) -> Settings`.
- Produces an importable `eduagent` package from `src` and a Streamlit entry point that renders a setup screen.

- [ ] **Step 1: Write configuration tests first**

```python
def test_settings_read_provider_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    settings = Settings.from_sources()
    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "test-model"
    assert settings.llm_configured is True


def test_settings_reports_missing_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Settings.from_sources()
    assert settings.llm_configured is False
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `python -m pytest tests/test_config.py -q`

Expected: FAIL because the package and `Settings` do not exist yet.

- [ ] **Step 3: Write the minimal bootstrap**

Use a frozen dataclass with defaults for non-secret settings:

```python
@dataclass(frozen=True)
class Settings:
    data_dir: Path
    runtime_dir: Path
    database_path: Path
    chroma_path: Path
    openai_api_key: str | None
    openai_base_url: str | None
    openai_model: str
    embedding_model: str
    retrieval_top_k: int = 5
    student_id: str = "demo_student"

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key and self.openai_model)
```

Configure `pyproject.toml` with `pythonpath = ["src"]`, Ruff line length 100, and project name `eduagent`. Keep `app.py` as a small bootstrap that inserts `src` on `sys.path`, loads `.env` when present, and shows a friendly missing-key setup message.

- [ ] **Step 4: Run focused tests and syntax checks**

Run: `python -m pytest tests/test_config.py -q`

Expected: PASS.

Run: `python -m compileall -q app.py src tests`

Expected: exit code 0.

- [ ] **Step 5: Commit the bootstrap**

```bash
git add app.py pyproject.toml requirements.txt requirements-dev.txt .env.example .gitignore .streamlit data src tests
git commit -m "build: bootstrap EduAgent package"
```

### Task 2: Implement page-aware PDF parsing, chunking, and ingestion

**Files:**
- Modify: `src/eduagent/models.py`
- Create: `src/eduagent/document_processing/parser.py`
- Create: `src/eduagent/document_processing/chunker.py`
- Create: `src/eduagent/document_processing/ingestion.py`
- Test: `tests/test_models.py`, `tests/test_parser.py`, `tests/test_chunker.py`, `tests/test_ingestion.py`

**Interfaces:**
- `parse_pdf(file_name: str, pdf_bytes: bytes) -> list[PageText]`.
- `chunk_pages(pages: Sequence[PageText], max_chars: int = 1000, overlap: int = 150) -> list[DocumentChunk]`.
- `IngestionService.ingest(file_name: str, pdf_bytes: bytes) -> IngestionResult`.
- `IngestionResult` contains `status`, `document_hash`, `page_count`, `chunk_count`, and a user-safe message.

- [ ] **Step 1: Write parser and chunker tests first**

```python
def test_parser_preserves_one_based_page_numbers(sample_pdf_bytes):
    pages = parse_pdf("lesson.pdf", sample_pdf_bytes)
    assert pages[0].page == 1
    assert "Bayes" in pages[0].text


def test_chunker_preserves_page_metadata_and_overlap():
    pages = [PageText(document_name="x.pdf", document_hash="h", page=3, text="abcdefghij")]
    chunks = chunk_pages(pages, max_chars=6, overlap=2)
    assert all(chunk.page == 3 for chunk in chunks)
    assert chunks[0].chunk_id != chunks[1].chunk_id
    assert chunks[0].text[-2:] == chunks[1].text[:2]


def test_empty_pdf_is_rejected(sample_empty_pdf_bytes):
    with pytest.raises(DocumentProcessingError, match="extractable text"):
        parse_pdf("empty.pdf", sample_empty_pdf_bytes)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_parser.py tests/test_chunker.py tests/test_ingestion.py -q`

Expected: FAIL because parsing, chunking, and ingestion services are not implemented.

- [ ] **Step 3: Implement the parser and chunker**

Use PyMuPDF with `fitz.open(stream=pdf_bytes, filetype="pdf")`; convert page indexes to one-based numbers and normalize whitespace with `re.sub(r"\\s+", " ", text).strip()`. Raise `DocumentProcessingError` for invalid PDFs, zero pages, or zero pages with usable text. Chunk each page independently so every chunk retains an unambiguous page citation. Use deterministic IDs derived from document hash, page, and chunk ordinal.

- [ ] **Step 4: Implement ingestion orchestration**

Hash raw bytes with SHA-256, consult the repository for an existing hash before parsing, then parse, chunk, embed, write to the vector store, and register the document. Return `duplicate` without re-embedding an existing document. Keep the service independent of Streamlit so it can be tested with fake embedding and storage objects.

- [ ] **Step 5: Run focused tests and commit**

Run: `python -m pytest tests/test_models.py tests/test_parser.py tests/test_chunker.py tests/test_ingestion.py -q`

Expected: PASS.

```bash
git add src/eduagent/models.py src/eduagent/document_processing tests/test_models.py tests/test_parser.py tests/test_chunker.py tests/test_ingestion.py
git commit -m "feat: add page-aware document ingestion"
```

### Task 3: Add the provider adapter, embeddings, Chroma storage, and retrieval

**Files:**
- Modify: `src/eduagent/config.py`, `src/eduagent/models.py`
- Create: `src/eduagent/llm/provider.py`
- Create: `src/eduagent/retrieval/embeddings.py`
- Create: `src/eduagent/retrieval/vector_store.py`
- Create: `src/eduagent/retrieval/retriever.py`
- Test: `tests/test_retrieval.py`

**Interfaces:**
- `EmbeddingProvider.embed(texts: Sequence[str]) -> list[list[float]]`.
- `LLMProvider.complete_text(system: str, user: str, *, temperature: float = 0.2) -> str`.
- `LLMProvider.complete_json(model_type: type[T], system: str, user: str, *, temperature: float = 0.2) -> T`.
- `ChromaVectorStore.add(chunks: Sequence[DocumentChunk], embeddings: Sequence[Sequence[float]]) -> None`.
- `ChromaVectorStore.search(query_embedding: Sequence[float], k: int) -> list[RetrievedChunk]`.
- `Retriever.retrieve(query: str, k: int | None = None) -> list[RetrievedChunk]`.
- `Retriever.format_context(results: Sequence[RetrievedChunk]) -> str`.

- [ ] **Step 1: Write fake-provider and retrieval tests first**

```python
def test_retriever_returns_metadata_and_excerpt(fake_vector_store):
    retriever = Retriever(embedding_provider=FakeEmbeddings(), vector_store=fake_vector_store, top_k=3)
    results = retriever.retrieve("What is MAP classification?")
    assert results[0].chunk.page == 12
    assert "lecture_05.pdf — Page 12" in retriever.format_context(results)


def test_missing_key_raises_safe_provider_error():
    with pytest.raises(ProviderConfigurationError, match="OPENAI_API_KEY"):
        OpenAICompatibleProvider(api_key=None, model="model", embedding_model="embed")
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest tests/test_retrieval.py -q`

Expected: FAIL because provider, fake contracts, and retrieval classes are not implemented.

- [ ] **Step 3: Implement provider and embedding adapters**

Use the OpenAI client with an optional `base_url`. Keep calls synchronous and bounded. The provider must never log prompts or returned student content. For `complete_json`, request a JSON object, validate with `model_type.model_validate_json`, and make one JSON-only repair request if validation fails; after the repair fails, raise `StructuredOutputError`.

Define `OpenAIEmbeddingProvider` as a thin adapter over `client.embeddings.create(model=..., input=list(texts))`. Reject an empty input list and verify that the returned vector count equals the input count.

- [ ] **Step 4: Implement Chroma storage and retrieval**

Create a persistent Chroma client under `Settings.chroma_path`, use collection `eduagent_course`, configure cosine distance, and write each chunk's text plus `document_name`, `document_hash`, `page`, and `chunk_id` metadata. Convert query results back to `RetrievedChunk`; calculate similarity as `1 - distance` when a distance is returned. Return an empty list for an uninitialized collection.

- [ ] **Step 5: Re-run tests and commit**

Run: `python -m pytest tests/test_retrieval.py -q`

Expected: PASS without a network request.

```bash
git add src/eduagent/config.py src/eduagent/models.py src/eduagent/llm src/eduagent/retrieval tests/test_retrieval.py
git commit -m "feat: add provider-backed course retrieval"
```

### Task 4: Implement the transparent learner model and SQLite repository

**Files:**
- Modify: `src/eduagent/models.py`
- Create: `src/eduagent/student/profile.py`
- Create: `src/eduagent/student/repository.py`
- Test: `tests/test_profile.py`, `tests/test_repository.py`

**Interfaces:**
- `update_concept_state(previous: ConceptState | None, score: float, correct: bool, now: datetime) -> ConceptState`.
- `weak_concepts(states: Iterable[ConceptState], threshold: float = 0.60) -> list[ConceptState]`.
- `StudentRepository.initialize() -> None`.
- `StudentRepository.get_profile(student_id: str) -> StudentProfile`.
- `StudentRepository.set_explanation_level(student_id: str, level: ExplanationLevel) -> None`.
- `StudentRepository.record_interaction(student_id: str, question: str, answer: str) -> None`.
- `StudentRepository.record_attempt(student_id: str, quiz: QuizQuestion, submitted_answer: str, evaluation: AnswerEvaluation) -> ConceptState`.
- `StudentRepository.list_concept_states(student_id: str) -> list[ConceptState]`.
- `StudentRepository.list_weak_concepts(student_id: str) -> list[ConceptState]`.
- `StudentRepository.overview(student_id: str) -> OverviewMetrics`.
- `StudentRepository.list_documents() -> list[IndexedDocument]`.

- [ ] **Step 1: Write mastery and persistence tests first**

```python
def test_first_attempt_uses_score_as_mastery():
    state = update_concept_state(None, score=0.8, correct=True, now=FIXED_NOW)
    assert state.mastery == pytest.approx(0.8)
    assert state.attempts == 1


def test_later_attempt_uses_transparent_weighting(previous_state):
    state = update_concept_state(previous_state, score=0.2, correct=False, now=FIXED_NOW)
    assert state.mastery == pytest.approx(0.70 * previous_state.mastery + 0.30 * 0.2)


def test_repository_persists_attempt_and_weak_concept(tmp_path, quiz, evaluation):
    repo = StudentRepository(tmp_path / "eduagent.db")
    repo.initialize()
    repo.record_attempt("demo_student", quiz, "partial answer", evaluation)
    assert repo.list_weak_concepts("demo_student")[0].concept == quiz.concept
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_profile.py tests/test_repository.py -q`

Expected: FAIL because profile functions and the SQLite repository are absent.

- [ ] **Step 3: Implement pure mastery functions**

Validate scores into `[0, 1]`, compute the specified weighted update, maintain arithmetic average and correct-attempt counts, and use ISO 8601 UTC timestamps. Do not add unrequested difficulty or recency modifiers.

- [ ] **Step 4: Implement the SQLite repository**

Create tables with `CREATE TABLE IF NOT EXISTS`, use `sqlite3.Row`, parameterized SQL, and explicit commits. Store quiz/evaluation JSON in `quiz_attempts`, maintain one row per `(student_id, concept)` in `concept_states`, and expose overview counts for interactions, quizzes, average score, and practiced concepts. Add `document_exists(document_hash)` and `register_document(...)` for ingestion duplicate checks.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest tests/test_profile.py tests/test_repository.py -q`

Expected: PASS.

```bash
git add src/eduagent/models.py src/eduagent/student tests/test_profile.py tests/test_repository.py
git commit -m "feat: add learner profile persistence"
```

### Task 5: Implement teaching policy, quiz generation, evaluation, and tutor composition

**Files:**
- Create: `src/eduagent/tutor/teaching_policy.py`
- Create: `src/eduagent/tutor/quiz_generator.py`
- Create: `src/eduagent/tutor/answer_evaluator.py`
- Create: `src/eduagent/tutor/tutor_agent.py`
- Test: `tests/test_teaching_policy.py`, `tests/test_tutor.py`

**Interfaces:**
- `TeachingPolicy.choose(concept: str, states: Mapping[str, ConceptState], recent_score: float | None) -> TeachingDecision`.
- `QuizGenerator.generate(topic: str, question_type: QuestionType, difficulty: Difficulty, context: str, source_ids: Sequence[str]) -> QuizQuestion`.
- `AnswerEvaluator.evaluate(quiz: QuizQuestion, submitted_answer: str, context: str) -> AnswerEvaluation`.
- `TutorAgent.answer_question(question: str, level: ExplanationLevel, profile: Sequence[ConceptState]) -> TutorResponse`.
- `TutorAgent.generate_quiz(topic: str, question_type: QuestionType, difficulty: Difficulty, profile: Sequence[ConceptState]) -> QuizQuestion`.
- `TutorAgent.evaluate_answer(quiz: QuizQuestion, submitted_answer: str, profile: Sequence[ConceptState]) -> tuple[AnswerEvaluation, TeachingDecision]`.

- [ ] **Step 1: Write policy and fake-provider tutor tests first**

```python
def test_policy_explains_new_concept():
    decision = TeachingPolicy().choose("MAP classification", {}, recent_score=None)
    assert decision.action is TeachingAction.EXPLAIN


def test_policy_reviews_low_mastery():
    state = ConceptState(
        concept="Bayes Rule", attempts=2, correct_attempts=0,
        average_score=0.2, mastery=0.2, last_score=0.2,
        last_practiced=FIXED_NOW,
    )
    decision = TeachingPolicy().choose("Bayes Rule", {"Bayes Rule": state}, recent_score=0.2)
    assert decision.action is TeachingAction.REVIEW_PREREQUISITE


def test_tutor_attaches_retrieved_sources(fake_provider, fake_retriever):
    response = TutorAgent(fake_provider, fake_retriever, TeachingPolicy()).answer_question(
        "What is MAP classification?", ExplanationLevel.STANDARD, []
    )
    assert response.answer
    assert response.sources[0].page == 12
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_teaching_policy.py tests/test_tutor.py -q`

Expected: FAIL because policy and tutor services are absent.

- [ ] **Step 3: Implement the deterministic policy**

Use the exact precedence from the spec: no attempt → `EXPLAIN`; mastery `< 0.40` → `REVIEW_PREREQUISITE`; latest score `< 0.50` → `GIVE_EXAMPLE`; mastery `< 0.75` → `GENERATE_QUIZ`; otherwise → `INCREASE_DIFFICULTY`. Return a one-sentence reason assembled by application logic.

- [ ] **Step 4: Implement grounded quiz and evaluation services**

Build prompts from retrieved context, selected explanation level, topic, question type, difficulty, and source IDs. Validate returned Pydantic objects. Ensure quiz source IDs are restricted to retrieved source IDs; the service must not accept an invented citation. For evaluation, reject provider scores outside `[0, 1]` with a schema error rather than silently correcting them. The policy-selected action replaces any model-suggested action in the final tutor result.

- [ ] **Step 5: Implement `TutorAgent` composition**

For Q&A, retrieve top-k chunks, return an evidence-limit response if none are available, call the provider for answer text, and attach `SourceReference` objects generated from retrieved chunks. For quiz generation and answer evaluation, use the same retriever and policy. Do not expose hidden chain-of-thought or raw prompts.

- [ ] **Step 6: Run tests and commit**

Run: `python -m pytest tests/test_teaching_policy.py tests/test_tutor.py -q`

Expected: PASS without network access.

```bash
git add src/eduagent/tutor tests/test_teaching_policy.py tests/test_tutor.py
git commit -m "feat: add adaptive tutor loop"
```

### Task 6: Build the complete Streamlit user experience

**Files:**
- Modify: `app.py`
- Create: `src/eduagent/ui/pages.py`
- Modify: `src/eduagent/config.py`, `src/eduagent/student/repository.py`
- Test: `tests/test_repository.py` and manual Streamlit smoke checks

**Interfaces:**
- `build_services(settings: Settings) -> AppServices`.
- `render_course_materials(services: AppServices) -> None`.
- `render_learn(services: AppServices) -> None`.
- `render_practice(services: AppServices) -> None`.
- `render_progress(services: AppServices) -> None`.
- `render_about() -> None`.

- [ ] **Step 1: Add service-container construction**

Create an `AppServices` dataclass containing settings, repository, vector store, embedding provider, retriever, LLM provider, ingestion service, and tutor agent. Initialize SQLite schema once and use `st.cache_resource` for the container. If credentials are absent, retain document-management and About pages but disable provider-dependent actions.

- [ ] **Step 2: Implement Course Materials and Learn pages**

Course Materials must accept `accept_multiple_files=True`, call ingestion only after an explicit button click, show per-file status, list indexed documents, and explain that uploads remain local. Learn must keep chat messages in `st.session_state`, record successful interactions, show source expanders, expose the three explanation levels, and show the deterministic teaching decision in an expander.

- [ ] **Step 3: Implement Practice and Progress pages**

Practice must offer weak-concept selection, topic entry, multiple-choice/short-answer type, difficulty, quiz generation, answer submission, and a clear feedback panel. After evaluation, call `record_attempt` exactly once, refresh profile state, and show the policy-selected next action. Progress must show four overview metrics, mastery percentages, weak concepts with Review actions, and recent quiz activity.

- [ ] **Step 4: Implement About and friendly error states**

Use `st.warning`, `st.error`, and `st.info` for missing keys, empty indexes, invalid files, duplicate files, and provider failures. Catch only expected domain exceptions in the UI; do not render tracebacks. About must distinguish implemented capability, future evaluation, and current limitations.

- [ ] **Step 5: Run local UI smoke checks**

Run: `streamlit run app.py --server.headless true --server.port 8501`

Expected: the process starts without import errors. In a second shell run:

```bash
curl -fsS http://localhost:8501/healthz
```

Expected: HTTP 200. Open the app manually and verify all five navigation labels render; without a key, verify the setup warning replaces model actions instead of a traceback.

- [ ] **Step 6: Commit the UI**

```bash
git add app.py src/eduagent/ui src/eduagent/config.py src/eduagent/student/repository.py
git commit -m "feat: add Streamlit learning interface"
```

### Task 7: Add demo content, evaluation tooling, and portfolio documentation

**Files:**
- Create: `examples/sample_course.md`
- Create: `examples/create_sample_pdf.py`
- Create: `examples/sample_course.pdf`
- Create: `examples/evaluation_dataset.json`
- Create: `src/eduagent/evaluation/rag_evaluator.py`
- Create: `docs/architecture.md`
- Create: `docs/demo.md`
- Create: `docs/impact_study.md`
- Create: `docs/cv_material.md`
- Create: `README.md`
- Test: `tests/test_retrieval.py`, evaluator CLI smoke test

**Interfaces:**
- `evaluate_dataset(dataset_path: Path, retriever: Retriever, answer_fn: Callable[[str, Sequence[RetrievedChunk]], str] | None = None) -> EvaluationReport`.
- CLI: `python -m eduagent.evaluation.rag_evaluator --dataset examples/evaluation_dataset.json`.

- [ ] **Step 1: Write the evaluation fixture and evaluator test**

```python
def test_evaluation_reports_source_hit_rate(tmp_path, fake_retriever):
    dataset = tmp_path / "eval.json"
    dataset.write_text(json.dumps([{
        "question": "What is MAP classification?",
        "expected_answer": "The most probable class",
        "expected_source": "sample_course.pdf",
        "expected_page": 2,
    }]))
    report = evaluate_dataset(dataset, fake_retriever)
    assert report.total_questions == 1
    assert report.retrieval_hit_rate == pytest.approx(1.0)
```

- [ ] **Step 2: Implement evaluator and sample content**

Keep metrics technical: top-k source hit rate, source recall, latency, and provider/generation failures. Generate a copyright-safe PDF from self-authored material covering probability, Bayes Rule, MAP classification, and maximum likelihood. Use the generated PDF's actual page layout when writing expected page numbers.

- [ ] **Step 3: Write portfolio documentation from implemented facts**

README must include exact setup commands, configuration, Mermaid architecture, feature list, limitations, deployment instructions, evaluation honesty, and a screenshot checklist. `docs/demo.md` must give a two-to-three-minute flow. `docs/architecture.md` must explain interfaces and data flow. `docs/impact_study.md` must describe a future pre/post-test design without results. `docs/cv_material.md` must contain only truthful bullets supported by the repository.

- [ ] **Step 4: Run documentation and evaluator checks**

Run: `python examples/create_sample_pdf.py`

Expected: `examples/sample_course.pdf` exists and opens with PyMuPDF.

Run: `python -m eduagent.evaluation.rag_evaluator --dataset examples/evaluation_dataset.json`

Expected: a JSON or table report is printed with technical metrics and no invented learning result.

- [ ] **Step 5: Commit documentation and demo assets**

```bash
git add README.md docs examples src/eduagent/evaluation
git commit -m "docs: add demo, evaluation, and deployment materials"
```

### Task 8: Perform final verification and deployment-readiness review

**Files:**
- Modify: `README.md`, `.env.example`, `requirements.txt`, `.gitignore`, or source files only when verification exposes a concrete mismatch.
- Test: all `tests/`, compile check, Ruff check, Streamlit smoke check, Git/privacy checks.

- [ ] **Step 1: Install the documented environment**

Run:

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
```

Expected: dependencies install without requiring an API key.

- [ ] **Step 2: Run all deterministic tests and static checks**

Run:

```bash
python -m pytest -q
ruff check .
python -m compileall -q app.py src tests
```

Expected: pytest passes, Ruff reports no errors, and compilation exits 0.

- [ ] **Step 3: Run the headless application check**

Run:

```bash
streamlit run app.py --server.headless true --server.port 8501
curl -fsS http://localhost:8501/healthz
```

Expected: Streamlit remains running, `/healthz` returns 200, and application logs contain no import traceback. Stop the process after the check.

- [ ] **Step 4: Verify Git and secret hygiene**

Run:

```bash
git status --short
git ls-files | rg '(^|/)(\.env|data/runtime|.*\.db$|.*\.sqlite$)' || true
rg -n 'sk-[A-Za-z0-9]' --glob '!docs/superpowers/**' --glob '!*.md' . || true
```

Expected: runtime data and secrets are not tracked, and no provider key appears in source.

- [ ] **Step 5: Update README with actual verification results**

Record only tests and checks actually run. State that deployment is “prepared” until a real Streamlit Cloud URL is confirmed. If no API key is available, list the exact remaining manual action: add `OPENAI_API_KEY`, `OPENAI_MODEL`, and optional `OPENAI_BASE_URL`/`OPENAI_EMBEDDING_MODEL`, then perform one real upload → question → quiz → evaluation flow.

- [ ] **Step 6: Commit final verification adjustments**

```bash
git add .
git commit -m "chore: verify EduAgent MVP readiness"
```

## Plan self-review checklist

- [ ] Spec coverage: ingestion, citations, explanation levels, quizzes, evaluation, mastery, weak concepts, policy, dashboard, observability, evaluation, deployment, privacy, tests, README, demo, architecture, and CV material each map to a task above.
- [ ] Placeholder scan: no step relies on “TBD”, “TODO”, “implement later”, or unspecified test behavior.
- [ ] Type consistency: `Settings`, `DocumentChunk`, `RetrievedChunk`, `QuizQuestion`, `AnswerEvaluation`, `StudentRepository`, `Retriever`, `LLMProvider`, and `TeachingPolicy` signatures are defined before use.
- [ ] Scope check: no P2 feature is required for the P0 acceptance criteria.
- [ ] Verification check: every task has a focused test or smoke command and a commit boundary.
