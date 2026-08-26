"""Application service wiring for the Streamlit runtime."""

from __future__ import annotations

from dataclasses import dataclass

from eduagent.config import Settings
from eduagent.document_processing.ingestion import IngestionService
from eduagent.llm.provider import LLMProvider, OpenAICompatibleProvider
from eduagent.retrieval.embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from eduagent.retrieval.retriever import Retriever
from eduagent.retrieval.vector_store import ChromaVectorStore
from eduagent.student.repository import StudentRepository
from eduagent.tutor.teaching_policy import TeachingPolicy
from eduagent.tutor.tutor_agent import TutorAgent


@dataclass
class AppServices:
    """All long-lived services used by one Streamlit application process."""

    settings: Settings
    repository: StudentRepository
    vector_store: ChromaVectorStore
    llm_provider: LLMProvider | None
    embedding_provider: EmbeddingProvider | None
    retriever: Retriever | None
    ingestion: IngestionService | None
    tutor: TutorAgent | None
    policy: TeachingPolicy

    @property
    def model_configured(self) -> bool:
        return self.llm_provider is not None and self.retriever is not None


def build_services(settings: Settings) -> AppServices:
    """Initialize persistence and optional model services without network calls."""

    settings.ensure_runtime_directories()
    repository = StudentRepository(settings.database_path)
    repository.initialize()
    vector_store = ChromaVectorStore(settings.chroma_path)
    policy = TeachingPolicy()

    if not (settings.llm_configured and settings.embeddings_configured):
        return AppServices(
            settings=settings,
            repository=repository,
            vector_store=vector_store,
            llm_provider=None,
            embedding_provider=None,
            retriever=None,
            ingestion=None,
            tutor=None,
            policy=policy,
        )

    provider = OpenAICompatibleProvider(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        embedding_model=settings.embedding_model,
    )
    embedding_provider = OpenAIEmbeddingProvider(provider)
    retriever = Retriever(embedding_provider, vector_store, top_k=settings.retrieval_top_k)
    ingestion = IngestionService(embedding_provider, vector_store, repository)
    tutor = TutorAgent(provider, retriever, policy)
    return AppServices(
        settings=settings,
        repository=repository,
        vector_store=vector_store,
        llm_provider=provider,
        embedding_provider=embedding_provider,
        retriever=retriever,
        ingestion=ingestion,
        tutor=tutor,
        policy=policy,
    )
