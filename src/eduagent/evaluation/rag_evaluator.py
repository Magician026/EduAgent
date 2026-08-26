"""Small technical retrieval evaluator with an offline demo mode."""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from eduagent.document_processing.chunker import chunk_pages
from eduagent.document_processing.parser import parse_pdf
from eduagent.models import DocumentChunk, RetrievedChunk


class EvaluationReport:
    """Technical retrieval and optional generation metrics."""

    def __init__(
        self,
        total_questions: int,
        retrieval_hit_rate: float,
        source_recall: float,
        average_latency_ms: float,
        generation_success_rate: float | None,
        provider_errors: int,
    ) -> None:
        self.total_questions = total_questions
        self.retrieval_hit_rate = retrieval_hit_rate
        self.source_recall = source_recall
        self.average_latency_ms = average_latency_ms
        self.generation_success_rate = generation_success_rate
        self.provider_errors = provider_errors

    def model_dump(self) -> dict[str, Any]:
        return {
            "total_questions": self.total_questions,
            "retrieval_hit_rate": self.retrieval_hit_rate,
            "source_recall": self.source_recall,
            "average_latency_ms": self.average_latency_ms,
            "generation_success_rate": self.generation_success_rate,
            "provider_errors": self.provider_errors,
        }


def evaluate_dataset(
    dataset_path: Path,
    retriever,
    answer_fn: Callable[[str, Sequence[RetrievedChunk]], str] | None = None,
) -> EvaluationReport:
    """Evaluate expected source retrieval and optionally answer generation."""

    records = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Evaluation dataset must be a JSON list.")
    hits = 0
    source_hits = 0
    latencies: list[float] = []
    generation_attempts = 0
    generation_successes = 0
    provider_errors = 0
    for record in records:
        started = time.perf_counter()
        try:
            results = retriever.retrieve(record["question"])
            if any(
                result.chunk.document_name == record["expected_source"]
                and result.chunk.page == record["expected_page"]
                for result in results
            ):
                hits += 1
            if any(result.chunk.document_name == record["expected_source"] for result in results):
                source_hits += 1
            if answer_fn is not None:
                generation_attempts += 1
                answer = answer_fn(record["question"], results)
                if answer and answer.strip():
                    generation_successes += 1
        except Exception:
            provider_errors += 1
        finally:
            latencies.append((time.perf_counter() - started) * 1000)
    total = len(records)
    return EvaluationReport(
        total_questions=total,
        retrieval_hit_rate=hits / total if total else 0.0,
        source_recall=source_hits / total if total else 0.0,
        average_latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        generation_success_rate=(
            generation_successes / generation_attempts if generation_attempts else None
        ),
        provider_errors=provider_errors,
    )


class KeywordDemoRetriever:
    """Offline lexical retriever used only by the sample evaluation CLI."""

    def __init__(self, chunks: Sequence[DocumentChunk]) -> None:
        self.chunks = list(chunks)

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        query_words = {word.lower() for word in query.split() if len(word) > 2}
        scored = []
        for chunk in self.chunks:
            text_words = {word.lower().strip(".,:!?()") for word in chunk.text.split()}
            overlap = len(query_words & text_words)
            scored.append((overlap, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievedChunk(chunk=chunk, similarity=min(1.0, score / max(1, len(query_words))))
            for score, chunk in scored[:k]
        ]


def _build_demo_retriever() -> KeywordDemoRetriever:
    sample_pdf = Path(__file__).resolve().parents[3] / "examples" / "sample_course.pdf"
    pages = parse_pdf(sample_pdf.name, sample_pdf.read_bytes())
    return KeywordDemoRetriever(chunk_pages(pages, max_chars=1200, overlap=100))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EduAgent technical retrieval evaluation.")
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate_dataset(args.dataset, _build_demo_retriever())
    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()
