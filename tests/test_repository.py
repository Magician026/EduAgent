from eduagent.models import ExplanationLevel
from eduagent.student.repository import StudentRepository


def test_repository_persists_profile_and_explanation_level(tmp_path):
    repo = StudentRepository(tmp_path / "eduagent.db")
    repo.initialize()

    profile = repo.get_profile("demo_student")
    repo.set_explanation_level("demo_student", ExplanationLevel.ADVANCED)
    updated = repo.get_profile("demo_student")

    assert profile.explanation_level is ExplanationLevel.STANDARD
    assert updated.explanation_level is ExplanationLevel.ADVANCED


def test_repository_persists_attempt_and_weak_concept(tmp_path, quiz, evaluation):
    repo = StudentRepository(tmp_path / "eduagent.db")
    repo.initialize()

    repo.record_attempt("demo_student", quiz, "partial answer", evaluation)

    weak = repo.list_weak_concepts("demo_student")
    overview = repo.overview("demo_student")
    assert weak[0].concept == quiz.concept
    assert weak[0].attempts == 1
    assert overview.quizzes_completed == 1
    assert overview.concepts_practiced == 1
    assert overview.average_quiz_score == evaluation.score


def test_repository_registers_documents_by_hash(tmp_path):
    repo = StudentRepository(tmp_path / "eduagent.db")
    repo.initialize()

    assert repo.document_exists("hash") is False
    repo.register_document("lesson.pdf", "hash", page_count=3, chunk_count=8)

    assert repo.document_exists("hash") is True
    assert repo.list_documents()[0].document_name == "lesson.pdf"
