# EduAgent P0 MVP Design Specification

**Date:** 2026-08-26  
**Status:** Approved architecture; awaiting written-spec review  
**Project:** EduAgent — An Agentic AI Tutor for Personalized Course Learning

## 1. Goal

EduAgent is a single-process Streamlit application that turns uploaded lecture PDFs into a course-grounded learning loop:

```text
PDF → page-aware chunks → embeddings → local vector retrieval
                                      ↓
Student question → tutor response + citations
                                      ↓
Quiz → formative evaluation → mastery update → next teaching action
```

The P0 MVP is successful when a reviewer can upload a course PDF, ask a grounded question, generate a quiz, submit an answer, see structured formative feedback, observe a mastery update, and inspect the resulting progress dashboard.

## 2. Scope and non-goals

### Included

- Multiple PDF upload with duplicate detection.
- Page-preserving text extraction and chunk metadata.
- Course-grounded retrieval with document/page citations.
- Beginner, Standard, and Advanced explanation levels.
- Multiple-choice and short-answer quiz generation.
- Structured answer evaluation with score, missing points, misconceptions, and next action.
- SQLite-backed single-student learning profile and quiz history.
- Transparent deterministic teaching policy.
- Streamlit pages for Learn, Course Materials, Practice, Progress, and About.
- Technical retrieval evaluation format and metrics.
- Self-authored sample course PDF and two-to-three-minute demo documentation.
- Streamlit Community Cloud deployment configuration and honest limitations.

### Explicitly excluded from P0

- Authentication, multi-user accounts, and instructor dashboards.
- OCR, background workers, Redis, Celery, microservices, and Kubernetes.
- React or a separately deployed backend.
- Knowledge graphs, advanced knowledge tracing, spaced repetition, and multi-agent orchestration.
- A real educational impact study or claims about learning gains.
- Durable cloud storage beyond the local application filesystem.

## 3. Technology decisions

| Concern | Decision | Reason |
| --- | --- | --- |
| UI/runtime | Streamlit | Fastest path to a polished demonstrable product. |
| Language | Python, verified with Python 3.12 | Existing local environment and broad dependency compatibility. |
| PDF parsing | PyMuPDF | Fast page-level extraction without OCR. |
| LLM and embeddings | OpenAI-compatible API behind an adapter | Supports the requested environment variables and provider substitution. |
| Vector store | Chroma persistent local client | Simple local persistence and a clear retrieval interface without an external server. |
| Structured data | Pydantic models | Validated contracts for LLM output and domain objects. |
| Student persistence | SQLite via the standard library | No external database service; supports structured history queries. |
| Tests | pytest | Directly requested and suitable for deterministic modules. |
| Deployment | Streamlit Community Cloud preparation | Simplest target for this app shape. |

The application will isolate Chroma and the model provider behind interfaces. Tests will use an in-memory/fake implementation where possible, but the deployed configuration will use Chroma and the configured provider. No silent mock answer will be shown to users when production credentials are missing.

## 4. Repository layout

```text
EduAgent/
├── app.py
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   ├── .gitkeep
│   └── runtime/              # ignored user data, Chroma files, SQLite database
├── examples/
│   ├── sample_course.pdf
│   └── evaluation_dataset.json
├── docs/
│   ├── architecture.md
│   ├── demo.md
│   ├── cv_material.md
│   └── impact_study.md
├── src/eduagent/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── document_processing/
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   └── chunker.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── provider.py
│   ├── tutor/
│   │   ├── __init__.py
│   │   ├── tutor_agent.py
│   │   ├── quiz_generator.py
│   │   ├── answer_evaluator.py
│   │   └── teaching_policy.py
│   ├── student/
│   │   ├── __init__.py
│   │   ├── profile.py
│   │   └── repository.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   └── rag_evaluator.py
│   └── ui/
│       ├── __init__.py
│       └── pages.py
└── tests/
    ├── conftest.py
    ├── test_chunker.py
    ├── test_profile.py
    ├── test_repository.py
    ├── test_teaching_policy.py
    ├── test_models.py
    └── test_retrieval.py
```

`app.py` will only initialize services, maintain Streamlit session state, and route to page renderers. Runtime uploads, vector data, and SQLite files will not be committed.

## 5. Domain models and interfaces

The following models are the stable contracts between modules:

- `PageText(document_name, document_hash, page, text)`
- `DocumentChunk(document_name, document_hash, page, chunk_id, text)`
- `SourceReference(document_name, page, chunk_id, excerpt)`
- `TutorResponse(answer, sources)`
- `QuizQuestion(question, question_type, concept, difficulty, options, reference_answer, source_chunks)`
- `AnswerEvaluation(score, correct, feedback, misconceptions, missing_points, concept, recommended_action)`
- `ConceptState(concept, attempts, correct_attempts, average_score, mastery, last_score, last_practiced)`
- `TeachingDecision(action, reason, concept)`

The important service boundaries are:

```text
DocumentParser.parse(file_name, bytes) -> list[PageText]
Chunker.chunk(pages) -> list[DocumentChunk]
EmbeddingProvider.embed(texts) -> list[list[float]]
VectorStore.add(chunks, embeddings); VectorStore.search(query_embedding, k) -> list[DocumentChunk]
LLMProvider.generate_json(prompt, schema) -> validated Pydantic model
StudentRepository.record_attempt(...) -> ConceptState
TeachingPolicy.choose(profile, recent_evaluation) -> TeachingDecision
```

The tutor agent composes these services. It does not decide system policy through an unconstrained LLM call.

## 6. Document ingestion and retrieval

1. The user selects one or more PDFs in the Course Materials page.
2. Each file is hashed with SHA-256 before parsing.
3. Duplicate content hashes are skipped and reported as already indexed.
4. PyMuPDF extracts text page by page. Empty PDFs and PDFs with no extractable text are rejected with a user-facing message.
5. The chunker cleans repeated whitespace and creates bounded chunks with page metadata. A chunk never crosses page metadata silently; if a page is long, multiple chunks keep the same page number.
6. The embedding adapter sends chunk texts to the configured OpenAI-compatible embedding endpoint.
7. Chroma stores the embedding, chunk text, and metadata. The document manifest is also recorded in SQLite for the UI.
8. Retrieval embeds the student query and returns the top-k chunks using cosine distance.
9. The tutor prompt includes only retrieved excerpts and their source metadata. The model is told not to fabricate citations and to state when the course evidence is insufficient.

The UI displays each source as an expandable card with document name, page number, and a shortened retrieved excerpt.

## 7. LLM provider and structured generation

`OpenAICompatibleProvider` will use the official OpenAI Python client with configurable `api_key`, `base_url`, and model names. The default configuration is read from environment variables or Streamlit secrets; no secret is stored in source code.

The provider will support:

- chat generation for grounded explanations;
- embedding generation for documents and queries;
- JSON-object generation for quizzes and answer evaluation;
- one bounded repair attempt when a provider returns malformed JSON;
- sanitized diagnostic logging that excludes prompts, source text, and student answers.

Provider errors become application-level errors with concise UI messages. The app will distinguish missing credentials, network/API failures, empty responses, and schema validation failures in logs without displaying stack traces to ordinary users.

### Prompt contracts

Grounded Q&A prompts will require:

- use of retrieved course evidence;
- explicit distinction between course evidence and general knowledge;
- no unsupported source or page claims;
- a pedagogical explanation at the selected level;
- an honest insufficient-evidence response.

Quiz prompts will require a single validated question containing concept, difficulty, question type, answer information, and source chunk IDs. Evaluation prompts will require score, correctness, feedback, misconceptions, missing points, concept, and recommended action. The model's recommended action is advisory; the application policy remains authoritative.

## 8. Tutor agent and teaching policy

The tutor agent exposes three application operations:

- `answer_question(question, explanation_level, profile)`
- `generate_quiz(topic, question_type, difficulty, profile)`
- `evaluate_answer(quiz, student_answer, profile)`

Supported teaching actions:

```text
EXPLAIN
GIVE_EXAMPLE
ASK_DIAGNOSTIC_QUESTION
GENERATE_QUIZ
REVIEW_PREREQUISITE
REMEDIATE_WEAK_CONCEPT
INCREASE_DIFFICULTY
DECREASE_DIFFICULTY
CONTINUE_TOPIC
```

The deterministic policy uses the following precedence:

```text
if the concept has no prior attempt:
    EXPLAIN
elif mastery < 0.40:
    REVIEW_PREREQUISITE
elif the latest score < 0.50:
    GIVE_EXAMPLE
elif mastery < 0.75:
    GENERATE_QUIZ
else:
    INCREASE_DIFFICULTY
```

The policy returns a short reason such as “Recent performance is below 50%, so EduAgent recommends an example before another quiz.” This is shown in an observability expander. It is an application decision explanation, not hidden model reasoning.

Explanation levels are prompt controls:

- Beginner: intuitive language, prerequisites, concrete example, minimal jargon.
- Standard: normal university-level explanation.
- Advanced: formal definitions, equations where relevant, and deeper technical detail.

## 9. Student model and persistence

The MVP uses a transparent heuristic rather than claiming scientifically validated knowledge tracing.

For a concept score `s` in `[0, 1]`:

```text
first attempt:  mastery = s
later attempts: mastery = 0.70 × previous_mastery + 0.30 × s
average_score = arithmetic mean of all scores
weak concept = mastery < 0.60
```

SQLite tables:

- `student_profiles`: one demo student, selected explanation level, timestamps.
- `concept_states`: attempts, correct attempts, average score, mastery, latest score, latest practice time.
- `quiz_attempts`: question metadata, submitted answer, evaluation JSON, score, and timestamp.
- `interactions`: question/answer activity used for overview counts.
- `documents`: file hash, display name, page count, chunk count, and indexed timestamp.

The repository will use parameterized SQL and a small transaction boundary around each profile update. The schema is created automatically on first run.

## 10. Streamlit experience

Sidebar navigation:

- **Learn:** chat-style grounded Q&A, source expanders, explanation-level selector, and teaching-decision explanation.
- **Course Materials:** multi-file upload, indexing action, duplicate/invalid-file feedback, and indexed document list.
- **Practice:** topic selection, weak-concept shortcut, quiz type/difficulty selection, answer submission, formative feedback, and next action.
- **Progress:** question count, quiz count, average score, practiced concepts, mastery table/chart, weak concepts, and recent activity.
- **About:** architecture, responsible-use statement, limitations, and evaluation distinction.

Streamlit session state will hold the current chat display and active quiz. SQLite remains the source of truth for profile and history. A single default student ID is sufficient for P0.

## 11. Evaluation

The repository will include a small JSON evaluation dataset with question, expected answer, expected source document, and expected page. The evaluator will report:

- retrieval hit rate at top-k;
- expected-source recall;
- structured answer-generation success;
- per-query latency;
- provider errors.

Any LLM-as-a-judge capability, if added, will be labeled explicitly and will not be presented as a measured educational outcome.

`docs/impact_study.md` will describe a future pre-test/post-test pilot with control/treatment assignment, learning gain calculation, completion time, satisfaction, ethics, privacy, and limitations. No study results will be claimed.

## 12. Error handling and privacy

- Missing API key: show setup instructions and disable model-dependent actions.
- API failure: show a retryable user message and log sanitized provider diagnostics.
- Invalid or empty PDF: reject only that file and continue processing valid files.
- Duplicate upload: skip by content hash and show the existing document.
- Empty vector store: explain that course materials must be indexed first.
- No useful retrieval: answer with an evidence limitation rather than inventing a citation.
- Malformed structured output: perform one repair attempt, then show a safe failure message.
- Uploaded files and runtime databases: stored only under ignored `data/runtime/`.
- Keys: loaded only from environment variables or Streamlit secrets.
- No unnecessary personal information is collected.

The README will warn that local uploads and the local SQLite database are not a substitute for production privacy controls and that Streamlit Community Cloud storage may be ephemeral.

## 13. Implementation milestones

1. Create package skeleton, config, models, dependency files, and basic Streamlit shell.
2. Implement PDF parser, chunker, Chroma adapter, provider adapter, and grounded Q&A.
3. Implement structured quiz generation and answer evaluation.
4. Implement SQLite repository, mastery heuristic, weak-concept detection, and teaching policy.
5. Integrate all Streamlit pages and session state.
6. Add sample course PDF, technical evaluation command, documentation, and deployment files.
7. Run tests, compile checks, headless Streamlit smoke test, and Git/privacy checks.

Each milestone will be tested before moving to the next. External API verification will be explicitly separated from offline/fake-provider verification.

## 14. Acceptance criteria

The MVP can be accepted when all of the following are true:

1. `streamlit run app.py` starts without import errors in the documented environment.
2. A valid sample or user PDF can be indexed with page metadata.
3. A grounded question returns an answer and visible source references when credentials are configured.
4. A quiz can be generated as a validated structured object.
5. A submitted answer returns structured formative feedback.
6. The concept mastery and quiz history persist after a Streamlit rerun.
7. The teaching policy chooses deterministic actions covered by tests.
8. The Progress page shows the required overview, mastery, weak concepts, and recent activity.
9. Missing keys, invalid PDFs, duplicates, empty indexes, and provider failures are handled without ordinary-user stack traces.
10. The test suite passes and README commands match the actual repository.
11. No secrets, uploaded course files, or runtime databases are tracked by Git.
12. Deployment is documented as prepared, not claimed as completed until a real public URL exists.

## 15. Manual actions remaining after implementation

The user will need to provide an API key through local environment variables or Streamlit Community Cloud secrets, run one real-provider smoke test, and perform the actual deployment. Screenshots will be taken after the deployed app is available.
