import json

import pytest

from eduagent.evaluation.rag_evaluator import evaluate_dataset
from eduagent.models import DocumentChunk, RetrievedChunk


class FakeRetriever:
    def retrieve(self, query, k=None):
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    document_name="sample_course.pdf",
                    document_hash="hash",
                    page=2,
                    chunk_id="chunk-2",
                    text="MAP classification chooses the highest posterior class.",
                ),
                similarity=0.9,
            )
        ]


def test_evaluation_reports_source_hit_rate(tmp_path):
    dataset = tmp_path / "eval.json"
    dataset.write_text(
        json.dumps(
            [
                {
                    "question": "What is MAP classification?",
                    "expected_answer": "The most probable class",
                    "expected_source": "sample_course.pdf",
                    "expected_page": 2,
                }
            ]
        ),
        encoding="utf-8",
    )

    report = evaluate_dataset(dataset, FakeRetriever())

    assert report.total_questions == 1
    assert report.retrieval_hit_rate == pytest.approx(1.0)
    assert report.source_recall == pytest.approx(1.0)
    assert report.generation_success_rate is None
