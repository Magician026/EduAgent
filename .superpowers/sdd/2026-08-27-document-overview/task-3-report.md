# Task 3 report — end-to-end regression and documentation

## Delivered

- Added a `TutorAgent` boundary regression using a fake provider and retriever.
  It confirms a broad document query uses overview retrieval, includes both
  contents and later-chapter context in the model request, and returns every
  source for the existing renderer.
- Updated English and Simplified Chinese README guidance: broad document
  questions use structure-aware distributed overview context; focused questions
  retain configured Top-K retrieval. Both state that page citations are
  evidence and the MVP does not replace source reading or expert judgment.

## Verification

- `PYTHON_DOTENV_DISABLED=true .venv/bin/pytest -q tests/test_tutor.py` — 5 passed.
- `PYTHON_DOTENV_DISABLED=true .venv/bin/pytest -q` — 46 passed.
- `.venv/bin/ruff check .` — passed.
- `.venv/bin/python -m compileall -q app.py src tests` — passed.
- `git diff --check` — passed.
- Read-only real-PDF check found 1,226 indexed chunks and 32 overview chunks,
  including contents pages 10–16 and later pages through 400.
- The Course Materials renderer displayed the already indexed `Analytic Learning
  Methods for Pattern Recognition.pdf` from the local runtime database.

## Scope

No production or retrieval files were modified. No PDF content, credentials, or
runtime data were added to Git.
