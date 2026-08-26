# Document Overview Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make broad document questions use structure-aware, page-grounded evidence from across the indexed PDF.

**Architecture:** Add deterministic document-overview intent detection and distributed chunk selection beside the existing nearest-neighbor retriever. Route only overview questions through that selector and use an overview-specific LLM prompt; focused questions remain unchanged.

**Tech Stack:** Python 3.11+, Streamlit, ChromaDB, PyMuPDF, Pydantic, existing OpenAI-compatible adapters, pytest.

**Spec:** `docs/superpowers/specs/2026-08-27-document-overview-design.md`

## Global Constraints

- No new runtime dependencies.
- Never send the full 1,226-chunk document in one LLM request.
- Keep ordinary retrieval at the configured `EDUAGENT_RETRIEVAL_TOP_K`.
- Use the existing OpenAI-compatible LLM and embedding adapters.
- Keep runtime data local; do not store PDF contents in Git or README files.
- Cap overview context to 32 chunks per document.

---

### Task 1: Structure-aware overview retrieval

**Files:**
- Create: `src/eduagent/retrieval/query_intent.py`
- Modify: `src/eduagent/retrieval/vector_store.py`
- Modify: `src/eduagent/retrieval/retriever.py`
- Test: `tests/test_retrieval.py`

**Interfaces:**
- Produces `is_document_overview_query(query: str) -> bool`.
- Produces `ChromaVectorStore.all_chunks() -> list[DocumentChunk]`.
- Produces `Retriever.retrieve_document_overview() -> list[RetrievedChunk]`.
- `Retriever.retrieve(query)` remains unchanged for focused questions.

- [ ] **Step 1: Write the failing tests**

```python
def test_document_overview_intent_detects_broad_question():
    assert is_document_overview_query("帮我介绍一下这个pdf讲了什么内容") is True


def test_document_overview_intent_keeps_focused_question_on_normal_path():
    assert is_document_overview_query("什么是 XGBoost？") is False


def test_document_overview_retrieval_spreads_evidence_across_document():
    def chunk(page, text):
        return DocumentChunk(
            document_name="book.pdf",
            document_hash="hash",
            page=page,
            chunk_id=f"chunk-{page}",
            text=text,
        )

    class FakeOverviewVectorStore:
        def __init__(self, chunks):
            self.chunks = chunks

        def all_chunks(self):
            return self.chunks

    retriever = Retriever(
        embedding_provider=FakeEmbeddings(),
        vector_store=FakeOverviewVectorStore(
            chunks=[
                chunk(page=1, text="Book title and author"),
                chunk(page=10, text="Contents 1 Introduction 5 Analytic Learning 89"),
                chunk(page=19, text="Chapter 1 Introduction Pattern Recognition"),
                chunk(page=89, text="Chapter 5 Analytic Learning"),
                chunk(page=161, text="Chapter 6 Penalized Learning"),
                chunk(page=266, text="Chapter 9 Ensemble Learning"),
                chunk(page=400, text="Appendix references"),
            ]
        ),
    )
    results = retriever.retrieve_document_overview()

    pages = {result.chunk.page for result in results}
    assert {10, 19, 89, 161, 266}.issubset(pages)
```

Run: `pytest tests/test_retrieval.py -q`  
Expected: FAIL because overview intent and distributed retrieval do not exist.

- [ ] **Step 2: Implement the smallest passing retrieval path**

Implement deterministic phrase detection, a Chroma read method that rebuilds
`DocumentChunk` objects from stored documents and metadata, and selection in
this order: contents signals, chapter-heading/summary signals, then evenly
spaced chunks. Deduplicate by `chunk_id` and enforce the 32-chunk cap per
document. Return overview chunks with neutral similarity scores.

- [ ] **Step 3: Run focused tests**

Run: `pytest tests/test_retrieval.py -q`  
Expected: PASS.

- [ ] **Step 4: Run lint and commit**

```bash
ruff check src/eduagent/retrieval tests/test_retrieval.py
git add src/eduagent/retrieval/query_intent.py src/eduagent/retrieval/vector_store.py src/eduagent/retrieval/retriever.py tests/test_retrieval.py
git commit -m "feat: add document overview retrieval"
```

### Task 2: Tutor routing and overview prompt

**Files:**
- Modify: `src/eduagent/tutor/tutor_agent.py`
- Test: `tests/test_tutor.py`

**Interfaces:**
- Consumes `is_document_overview_query` and `Retriever.retrieve_document_overview` from Task 1.
- `TutorAgent.answer_question` keeps its current signature and citation return type.

- [ ] **Step 1: Write the failing tests**

```python
def test_tutor_routes_broad_question_to_document_overview():
    response = tutor.answer_question(
        "帮我介绍一下这个pdf讲了什么内容",
        ExplanationLevel.STANDARD,
        [],
    )

    assert retriever.overview_calls == 1
    assert retriever.focused_calls == 0
    assert response.sources[0].page == 10
```

Run: `pytest tests/test_tutor.py -q`  
Expected: FAIL because the tutor always uses focused retrieval.

- [ ] **Step 2: Implement overview routing**

Select `retrieve_document_overview()` when the intent helper returns true.
Use an overview-specific system/user prompt that requests the document’s
purpose, table-of-contents/chapter structure, major topics or methods, and
page-grounded uncertainty handling. Keep the existing prompt for focused
questions.

- [ ] **Step 3: Run focused tests**

Run: `pytest tests/test_tutor.py -q`  
Expected: PASS.

- [ ] **Step 4: Run lint and commit**

```bash
ruff check src/eduagent/tutor tests/test_tutor.py
git add src/eduagent/tutor/tutor_agent.py tests/test_tutor.py
git commit -m "feat: route broad questions to document overview"
```

### Task 3: End-to-end regression and user-facing documentation

**Files:**
- Modify: `tests/test_tutor.py`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Interfaces:**
- Consumes the overview route from Tasks 1–2 without changing the Streamlit page layout.

- [ ] **Step 1: Add the regression test**

Exercise the real `TutorAgent` boundary with a fake provider and a retriever
that returns sources from both contents and later chapters. Assert that the
answer request includes the overview instruction, the overview retriever is
called instead of focused retrieval, and all sources remain available to the
existing response renderer.

- [ ] **Step 2: Update both READMEs**

Document that broad document questions use an overview path, while focused
questions use Top-K retrieval. State that page citations are evidence and the
MVP does not replace expert reading.

- [ ] **Step 3: Run the full verification suite**

```bash
PYTHON_DOTENV_DISABLED=true pytest -q
ruff check .
python -m compileall -q app.py src tests
git diff --check
```

- [ ] **Step 4: Run the real PDF regression**

Use the already indexed PDF at `/Users/magician/Desktop/MA ZIxian_G2601604D/课程/6406/Analytic Learning Methods for Pattern Recognition.pdf` and verify that the overview retrieval pages include the contents and later chapter ranges, then verify the Streamlit page still renders the indexed file.

- [ ] **Step 5: Commit and sync**

```bash
git add tests/test_pages.py README.md README.zh-CN.md
git commit -m "test: document whole-file overview behavior"
git push origin master
```
