from types import SimpleNamespace

from eduagent.models import IngestionResult
from eduagent.ui import pages


class _Status:
    def __init__(self, events, label):
        self.events = events
        self.label = label

    def __enter__(self):
        self.events.append(("status_start", self.label))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def write(self, message):
        self.events.append(("status_write", message))

    def update(self, **kwargs):
        self.events.append(("status_update", kwargs))


class _StreamlitRecorder:
    def __init__(self, events, uploaded_files):
        self.events = events
        self.uploaded_files = uploaded_files

    def header(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass

    def file_uploader(self, *args, **kwargs):
        return self.uploaded_files

    def button(self, *args, **kwargs):
        return True

    def status(self, label, **kwargs):
        return _Status(self.events, label)

    def spinner(self, label):
        return _Status(self.events, label)

    def success(self, message):
        self.events.append(("success", message))

    def info(self, message):
        self.events.append(("info", message))

    def error(self, message):
        self.events.append(("error", message))

    def subheader(self, *args, **kwargs):
        pass


class _Ingestion:
    def __init__(self, events):
        self.events = events

    def ingest(self, file_name, pdf_bytes, progress_callback=None):
        self.events.append(("ingest", file_name))
        if progress_callback is not None:
            progress_callback(1, 1)
        return IngestionResult(
            status="indexed",
            document_hash="hash",
            page_count=1,
            chunk_count=1,
            message=f"Indexed {file_name}.",
        )


class _Repository:
    def list_documents(self):
        return []


class _UploadedFile:
    name = "lesson.pdf"

    def getvalue(self):
        return b"pdf"


def test_course_materials_shows_live_status_before_indexing_call(monkeypatch):
    events = []
    uploaded_files = [_UploadedFile()]
    fake_streamlit = _StreamlitRecorder(events, uploaded_files)
    services = SimpleNamespace(
        ingestion=_Ingestion(events),
        repository=_Repository(),
        model_configured=True,
    )
    monkeypatch.setattr(pages, "st", fake_streamlit)

    pages.render_course_materials(services)

    event_names = [event[0] for event in events]
    assert event_names.index("status_start") < event_names.index("ingest")
    assert event_names.index("status_write") < event_names.index("ingest")
    assert any(
        event[0] == "status_write" and event[1] == "Embedding chunks: 1/1"
        for event in events
    )
    assert any(
        event[0] == "status_update" and event[1]["state"] == "complete"
        for event in events
    )
