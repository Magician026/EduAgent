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
from eduagent.ui.pages import (
    render_about,
    render_course_materials,
    render_learn,
    render_practice,
    render_progress,
    render_sidebar,
)
from eduagent.ui.services import AppServices, build_services


def _streamlit_secrets() -> dict[str, str]:
    """Return Streamlit secrets as a plain mapping without exposing values."""

    try:
        return {key: str(st.secrets[key]) for key in st.secrets}
    except Exception:
        return {}


@st.cache_resource(show_spinner=False)
def _get_services(settings: Settings) -> AppServices:
    return build_services(settings)


def main() -> None:
    """Render the complete EduAgent Streamlit application."""

    st.set_page_config(page_title="EduAgent", page_icon="🎓", layout="wide")
    settings = Settings.from_sources(secrets=_streamlit_secrets())
    settings.ensure_runtime_directories()

    services = _get_services(settings)
    page, level = render_sidebar(services)
    if page == "🏠 Learn":
        render_learn(services, level)
    elif page == "📚 Course Materials":
        render_course_materials(services)
    elif page == "🧠 Practice":
        render_practice(services)
    elif page == "📊 Progress":
        render_progress(services)
    else:
        render_about()


if __name__ == "__main__":
    main()
