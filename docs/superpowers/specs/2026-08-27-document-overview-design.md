# Document Overview Mode Design

**Date:** 2026-08-27
**Status:** Approved in conversation; implementation requested

## Problem

EduAgent currently uses nearest-neighbor retrieval with `top_k=5` for every
question. That is appropriate for focused questions, but a request such as
“帮我介绍一下这个 PDF 讲了什么内容” is a document-level task. The query
embedding is most similar to cover, title, and author pages, so the tutor sees
only front matter even though the full PDF has already been indexed.

## Goal

Route document-level overview questions through a structure-aware retrieval
path that supplies evidence from the document outline and representative
content across the whole document, then ask the configured LLM to produce a
page-grounded overview in the student’s language.

## Design

1. Detect document-overview intent using small, deterministic Chinese and
   English phrase rules. Focused questions keep the existing nearest-neighbor
   path unchanged.
2. Add a vector-store read boundary that returns all stored chunks and their
   page metadata without re-uploading the PDF or calling the embedding API.
3. Build a deterministic overview selection per document:
   - include chunks containing contents/目录/table-of-contents signals;
   - include chapter-heading and chapter-summary signals;
   - fill remaining capacity with evenly spaced chunks across the document;
   - deduplicate by chunk ID and cap context to 32 chunks per document.
4. Route overview questions to the selected evidence. The overview prompt
   explicitly asks for purpose, chapter structure, main topics/methods, and
   page references, and requires the model to state uncertainty when outline
   evidence is unavailable.
5. Preserve existing citation rendering and focused-question behavior.

## Constraints

- No new runtime dependencies.
- Never send the full 1,226-chunk document in one LLM request.
- Keep ordinary retrieval at the configured `EDUAGENT_RETRIEVAL_TOP_K`.
- Use the existing OpenAI-compatible LLM and embedding adapters.
- Keep runtime data local; do not store PDF contents in Git or README files.

## Acceptance Criteria

- The sample 400-page PDF’s broad overview query retrieves pages from its
  contents and later chapters, not only pages 1–4.
- A focused query still calls ordinary Top-K retrieval.
- The tutor routes broad Chinese and English overview questions through the
  overview path and returns sources with page numbers.
- Unit tests cover intent detection, distributed selection, routing, and the
  no-structure fallback.
- The real indexed PDF produces a useful overview without requiring a second
  upload or re-index.
