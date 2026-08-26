"""Streamlit page renderers for the EduAgent MVP."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd
import streamlit as st

from eduagent.document_processing.parser import DocumentProcessingError
from eduagent.llm.provider import ProviderError
from eduagent.models import (
    AnswerEvaluation,
    Difficulty,
    ExplanationLevel,
    QuestionType,
    QuizQuestion,
    SourceReference,
    TeachingDecision,
)
from eduagent.tutor.tutor_agent import NoRelevantContextError
from eduagent.ui.services import AppServices


def _model_ready_or_explain(services: AppServices) -> bool:
    if services.model_configured:
        return True
    st.warning(
        "模型功能尚未启用。请在 `.env` 或 Streamlit secrets 中设置 "
        "`EDUAGENT_LLM_API_KEY`、`EDUAGENT_LLM_MODEL`，以及可用的 "
        "`EDUAGENT_EMBEDDING_API_KEY`、`EDUAGENT_EMBEDDING_MODEL`。"
    )
    return False


def _render_sources(sources: Sequence[SourceReference | dict[str, Any]]) -> None:
    if not sources:
        return
    with st.expander(f"📚 来源（{len(sources)}）", expanded=False):
        for index, source in enumerate(sources, start=1):
            if isinstance(source, dict):
                source = SourceReference.model_validate(source)
            st.markdown(f"**{index}. {source.document_name} — Page {source.page}**")
            st.caption(source.excerpt)


def _render_decision(decision: TeachingDecision | None) -> None:
    if decision is None:
        return
    with st.expander("🔎 为什么选择这个教学动作？", expanded=False):
        st.markdown(f"**Selected action:** `{decision.action.value}`")
        st.write(decision.reason)


def _current_level(services: AppServices) -> ExplanationLevel:
    profile = services.repository.get_profile(services.settings.student_id)
    labels = list(ExplanationLevel)
    current_index = labels.index(profile.explanation_level)
    selected = st.sidebar.selectbox(
        "Explanation level",
        labels,
        index=current_index,
        format_func=lambda level: level.value,
    )
    if selected is not profile.explanation_level:
        services.repository.set_explanation_level(services.settings.student_id, selected)
    return selected


def render_course_materials(services: AppServices) -> None:
    """Render upload, indexing, and indexed-document status."""

    st.header("📚 Course Materials")
    st.write("Upload lecture PDFs to build a page-aware, searchable course knowledge base.")
    uploaded_files = st.file_uploader(
        "Choose one or more lecture PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if st.button("Index selected PDFs", type="primary", disabled=not uploaded_files):
        if services.ingestion is None:
            _model_ready_or_explain(services)
        else:
            indexed_count = 0
            duplicate_count = 0
            failed_count = 0
            with st.status(
                f"Indexing {len(uploaded_files)} PDF(s)…",
                expanded=True,
            ) as indexing_status:
                for file_number, uploaded_file in enumerate(uploaded_files, start=1):
                    indexing_status.write(
                        f"Processing {file_number}/{len(uploaded_files)}: {uploaded_file.name}"
                    )
                    try:
                        with st.spinner(f"Generating embeddings for {uploaded_file.name}…"):
                            result = services.ingestion.ingest(
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                            )
                        if result.status == "duplicate":
                            duplicate_count += 1
                            st.info(result.message)
                        else:
                            indexed_count += 1
                            st.success(result.message)
                    except DocumentProcessingError as exc:
                        failed_count += 1
                        st.error(f"{uploaded_file.name}: {exc}")
                    except ProviderError as exc:
                        failed_count += 1
                        st.error(f"{uploaded_file.name}: model service unavailable — {exc}")
                    except ValueError as exc:
                        failed_count += 1
                        st.error(f"{uploaded_file.name}: {exc}")
                    except Exception as exc:
                        failed_count += 1
                        st.error(f"{uploaded_file.name}: indexing failed — {exc}")

                if failed_count:
                    indexing_status.update(
                        label=(
                            f"Indexing finished with {failed_count} error(s): "
                            f"{indexed_count} indexed, {duplicate_count} already indexed."
                        ),
                        state="error",
                        expanded=True,
                    )
                else:
                    indexing_status.update(
                        label=(
                            f"Indexing complete: {indexed_count} indexed, "
                            f"{duplicate_count} already indexed."
                        ),
                        state="complete",
                        expanded=False,
                    )

    documents = services.repository.list_documents()
    st.subheader("Indexed files")
    if not documents:
        st.info("No course PDFs have been indexed yet.")
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Document": document.document_name,
                    "Pages": document.page_count,
                    "Chunks": document.chunk_count,
                    "Indexed at": document.indexed_at.strftime("%Y-%m-%d %H:%M UTC"),
                }
                for document in documents
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_learn(services: AppServices, level: ExplanationLevel) -> None:
    """Render the grounded chat tutoring page."""

    st.header("🏠 Learn")
    st.write(
        "Ask questions about your indexed course materials and inspect the retrieved evidence."
    )
    messages: list[dict[str, Any]] = st.session_state.setdefault("chat_messages", [])
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            _render_sources(message.get("sources", []))

    question = st.chat_input("Ask a question about the course")
    if question is None:
        return
    if services.tutor is None:
        _model_ready_or_explain(services)
        return
    with st.chat_message("user"):
        st.markdown(question)
    try:
        profile = services.repository.list_concept_states(services.settings.student_id)
        response = services.tutor.answer_question(question, level, profile)
        services.repository.record_interaction(
            services.settings.student_id,
            question,
            response.answer,
        )
        messages.extend(
            [
                {"role": "user", "content": question},
                {
                    "role": "assistant",
                    "content": response.answer,
                    "sources": [source.model_dump(mode="json") for source in response.sources],
                },
            ]
        )
        with st.chat_message("assistant"):
            st.markdown(response.answer)
            _render_sources(response.sources)
            weak = services.repository.list_weak_concepts(services.settings.student_id)
            focus = weak[0].concept if weak else question[:60]
            decision = services.policy.choose(
                focus,
                {state.concept: state for state in profile},
                None,
            )
            _render_decision(decision)
    except ProviderError as exc:
        st.error(f"模型服务暂时不可用：{exc}")


def _quiz_topic(services: AppServices) -> str:
    weak = services.repository.list_weak_concepts(services.settings.student_id)
    states = services.repository.list_concept_states(services.settings.student_id)
    choices = [state.concept for state in weak] + [
        state.concept for state in states if state.concept not in {item.concept for item in weak}
    ]
    if "practice_topic" not in st.session_state:
        st.session_state["practice_topic"] = choices[0] if choices else ""
    if choices:
        selected = st.selectbox(
            "Choose a practiced concept",
            choices,
            index=choices.index(st.session_state["practice_topic"])
            if st.session_state["practice_topic"] in choices
            else 0,
        )
        st.session_state["practice_topic"] = selected
    return st.text_input("Or enter a topic", key="practice_topic")


def _render_evaluation(evaluation: AnswerEvaluation, decision: TeachingDecision) -> None:
    score = f"{evaluation.score:.0%}"
    st.subheader(f"Formative feedback · {score}")
    st.write(evaluation.feedback)
    if evaluation.missing_points:
        st.markdown("**Missing key points**")
        st.write("; ".join(evaluation.missing_points))
    if evaluation.misconceptions:
        st.markdown("**Possible misconceptions**")
        st.write("; ".join(evaluation.misconceptions))
    _render_decision(decision)


def render_practice(services: AppServices) -> None:
    """Render quiz generation, submission, evaluation, and adaptation."""

    st.header("🧠 Practice")
    st.write("Generate a grounded question, submit an answer, and update your concept profile.")
    if services.tutor is None:
        _model_ready_or_explain(services)
        return

    topic = _quiz_topic(services)
    question_type = QuestionType(
        st.selectbox("Question type", [item.value for item in QuestionType])
    )
    difficulty = st.selectbox("Difficulty", list(Difficulty), format_func=lambda item: item.value)
    if st.button("Generate quiz", type="primary", disabled=not topic.strip()):
        try:
            quiz = services.tutor.generate_quiz(
                topic,
                question_type=question_type,
                difficulty=difficulty,
                profile=services.repository.list_concept_states(services.settings.student_id),
            )
            st.session_state["active_quiz"] = quiz
            st.session_state.pop("active_evaluation", None)
        except (ProviderError, NoRelevantContextError, ValueError) as exc:
            st.error(f"无法生成测验：{exc}")

    quiz: QuizQuestion | None = st.session_state.get("active_quiz")
    if quiz is None:
        st.info("选择一个概念后生成测验。")
        return
    st.divider()
    st.subheader(f"{quiz.concept} · {quiz.difficulty.value}")
    st.markdown(quiz.question)
    if quiz.question_type.value == "multiple_choice":
        answer = st.radio("Your answer", quiz.options, key="quiz_answer_choice")
    else:
        answer = st.text_area("Your answer", key="quiz_answer_text", height=140)

    if st.button("Submit answer", disabled=not answer.strip()):
        if "active_evaluation" not in st.session_state:
            try:
                evaluation, decision = services.tutor.evaluate_answer(
                    quiz,
                    answer,
                    services.repository.list_concept_states(services.settings.student_id),
                )
                services.repository.record_attempt(
                    services.settings.student_id,
                    quiz,
                    answer,
                    evaluation,
                )
                st.session_state["active_evaluation"] = evaluation
                st.session_state["active_decision"] = decision
            except ProviderError as exc:
                st.error(f"无法评估答案：{exc}")

    evaluation = st.session_state.get("active_evaluation")
    decision = st.session_state.get("active_decision")
    if evaluation is not None and decision is not None:
        _render_evaluation(evaluation, decision)


def render_progress(services: AppServices) -> None:
    """Render overview metrics, mastery, weak concepts, and recent activity."""

    st.header("📊 Progress")
    overview = services.repository.overview(services.settings.student_id)
    columns = st.columns(4)
    columns[0].metric("Questions asked", overview.questions_asked)
    columns[1].metric("Quizzes completed", overview.quizzes_completed)
    columns[2].metric("Average score", f"{overview.average_quiz_score:.0%}")
    columns[3].metric("Concepts practiced", overview.concepts_practiced)

    states = services.repository.list_concept_states(services.settings.student_id)
    st.subheader("Concept mastery")
    if states:
        dataframe = pd.DataFrame(
            [
                {
                    "Concept": state.concept,
                    "Mastery": f"{state.mastery:.0%}",
                    "Attempts": state.attempts,
                    "Average score": f"{state.average_score:.0%}",
                }
                for state in states
            ]
        )
        st.dataframe(dataframe, use_container_width=True, hide_index=True)
    else:
        st.info("Complete a quiz to see concept mastery here.")

    weak = services.repository.list_weak_concepts(services.settings.student_id)
    st.subheader("Weak concepts")
    if weak:
        for state in weak:
            left, right = st.columns([4, 1])
            left.write(f"**{state.concept}** — {state.mastery:.0%}")
            if right.button("Review", key=f"review_{state.concept}"):
                st.session_state["practice_topic"] = state.concept
                st.session_state["page"] = "🧠 Practice"
                st.rerun()
    else:
        st.success("No weak concepts identified yet.")

    st.subheader("Recent activity")
    attempts = services.repository.recent_attempts(services.settings.student_id)
    if attempts:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Concept": attempt["concept"],
                        "Score": f"{attempt['score']:.0%}",
                        "Correct": "Yes" if attempt["correct"] else "No",
                        "Time": attempt["created_at"],
                    }
                    for attempt in attempts
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No quiz activity yet.")


def render_about() -> None:
    """Explain the product, architecture, responsible use, and limitations."""

    st.header("ℹ️ About EduAgent")
    st.markdown(
        """
        EduAgent is an agentic AI tutor for personalized course learning. It combines
        course-grounded retrieval with a lightweight learner profile: the model writes
        explanations and feedback, while an interpretable application policy decides
        whether the next step should be explanation, an example, remediation, or a
        harder quiz.
        """
    )
    st.subheader("What is implemented")
    st.write(
        "PDF ingestion, page citations, grounded Q&A, structured quizzes, formative feedback, "
        "mastery tracking, weak-concept detection, and a progress dashboard."
    )
    st.subheader("Limitations")
    st.write(
        "The MVP is single-student, stores runtime data locally, uses a transparent heuristic "
        "rather than validated knowledge tracing, and does not establish educational learning "
        "gains."
    )
    st.subheader("Evaluation distinction")
    st.write(
        "Technical retrieval metrics are separate from a future pre-test/post-test learning-impact "
        "study. No student study results are included in this application."
    )


def render_sidebar(services: AppServices) -> tuple[str, ExplanationLevel]:
    """Render navigation and shared settings."""

    st.sidebar.title("EduAgent")
    pages = ["🏠 Learn", "📚 Course Materials", "🧠 Practice", "📊 Progress", "ℹ️ About"]
    current_page = st.session_state.get("page", pages[0])
    page = st.sidebar.radio("Navigate", pages, index=pages.index(current_page))
    st.session_state["page"] = page
    level = _current_level(services)
    if not services.model_configured:
        st.sidebar.warning("Add API credentials to enable tutor actions.")
    return page, level
