# EduAgent Two-to-Three-Minute Demo

## Demo setup

```bash
source .venv/bin/activate
python examples/create_sample_pdf.py
streamlit run app.py
```

Before the demo, configure the OpenAI-compatible API key in `.env` or Streamlit secrets. The sample course is self-authored and covers Bayes Rule, MAP classification, and maximum likelihood estimation.

## Script

1. **Course Materials — 20 seconds**
   - Upload `examples/sample_course.pdf`.
   - Click **Index selected PDFs**.
   - Point out page count, chunk count, and duplicate detection.

2. **Learn — 30 seconds**
   - Ask: “What is MAP classification?”
   - Show that the answer is based on course context.
   - Expand the source card and point to `sample_course.pdf — Page 2`.
   - Open the teaching-decision expander and explain that policy decisions are application-controlled.

3. **Practice — 45 seconds**
   - Choose `MAP classification` or enter the topic.
   - Generate a short-answer quiz.
   - Submit a partial answer such as “It chooses the most likely class.”
   - Show score, missing posterior-probability point, and formative feedback.

4. **Adaptive loop — 25 seconds**
   - Point out the updated mastery and the next action, such as `GIVE_EXAMPLE` or `GENERATE_QUIZ`.
   - Explain that the LLM writes feedback but the deterministic policy chooses the action.

5. **Progress — 20 seconds**
   - Show questions asked, quiz count, average score, concept mastery, weak concepts, and recent activity.

6. **About — 10 seconds**
   - State the limitations: single-student MVP, local persistence, formative evaluation, and no claimed learning study.

## Technical decisions to explain in an interview

### Why RAG instead of a general chatbot?

The course PDF is the source of truth for course-specific questions. Retrieval gives the model relevant evidence and lets the UI show page-aware citations. It also makes “not enough evidence” an explicit behavior.

### Why call this an agent?

The system closes a loop: it observes the student question or quiz answer, updates a learner state, chooses a teaching action, and produces the next intervention. It is more than question-to-answer retrieval.

### Why a deterministic policy instead of an autonomous multi-agent framework?

The MVP needs inspectable and testable adaptation. A deterministic policy makes thresholds, behavior, and debugging clear while keeping LLM generation focused on language and feedback.

### How is mastery calculated?

The first score becomes mastery. Later scores update mastery as `0.70 * previous + 0.30 * current`. This is a transparent MVP heuristic, not a validated knowledge-tracing model.

### What can go wrong in RAG?

PDF extraction can fail, chunks can omit context, embeddings can retrieve an adjacent concept, and the LLM can still overgeneralize. That is why citations, insufficient-evidence behavior, technical retrieval evaluation, and honest limitations are included.

### How would you evaluate educational impact?

Run a controlled pilot with pre-test, treatment/control assignment, learning session, post-test, learning gain, completion time, and satisfaction measures. The app itself does not claim such a result; the proposed design is in `docs/impact_study.md`.

### What would you improve next?

Add multi-course isolation, validated learner modeling, concept prerequisites, durable reviewed storage, instructor analytics, and a controlled study before making educational claims.
