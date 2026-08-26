"""EduAgent Streamlit entry point.

The full page service wiring is added in later milestones. This first shell is
deliberately useful on its own: it validates configuration and gives a clear
next action instead of exposing a traceback.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st

from eduagent.config import Settings


def _streamlit_secrets() -> dict[str, str]:
    """Return Streamlit secrets as a plain mapping without exposing values."""

    try:
        return {key: str(st.secrets[key]) for key in st.secrets}
    except Exception:
        return {}


def main() -> None:
    """Render the initial application shell."""

    st.set_page_config(page_title="EduAgent", page_icon="🎓", layout="wide")
    settings = Settings.from_sources(secrets=_streamlit_secrets())
    settings.ensure_runtime_directories()

    st.title("🎓 EduAgent")
    st.caption("An Agentic AI Tutor for Personalized Course Learning")

    if not settings.llm_configured:
        st.warning("模型服务尚未配置。请添加 OPENAI_API_KEY 后重新运行应用。")
        st.markdown(
            """
            EduAgent will turn course PDFs into a searchable learning workspace,
            then provide grounded explanations, quizzes, formative feedback, and
            a transparent next-teaching-action recommendation.
            """
        )
        st.code("cp .env.example .env\n# Edit .env and set OPENAI_API_KEY\nstreamlit run app.py")
        return

    st.success("模型配置已就绪。课程材料和学习页面将在后续里程碑启用。")


if __name__ == "__main__":
    main()
