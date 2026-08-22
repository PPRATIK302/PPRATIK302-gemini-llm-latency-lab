"""Local TF-IDF retrieval for transparent context-reduction demos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class SupportDocument:
    id: str
    title: str
    text: str


@dataclass(frozen=True)
class RetrievedPassage:
    document: SupportDocument
    score: float


def load_documents(path: Path) -> list[SupportDocument]:
    """Load sample support documents."""

    with path.open(encoding="utf-8") as handle:
        rows = json.load(handle)
    return [SupportDocument(**row) for row in rows]


class LocalTfidfRetriever:
    """Small local retriever used to teach context pruning, not production RAG."""

    def __init__(self, documents: list[SupportDocument]) -> None:
        self.documents = documents
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(
            f"{document.title}\n{document.text}" for document in documents
        )

    def search(self, query: str, *, top_k: int = 3) -> list[RetrievedPassage]:
        """Return the top-k documents ranked by cosine similarity."""

        if top_k <= 0:
            return []
        query_vector = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self._matrix).ravel()
        ordered = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            RetrievedPassage(document=self.documents[index], score=float(score))
            for index, score in ordered
        ]


def approximate_context_size(text: str) -> int:
    """Approximate context size in characters for simple before/after comparisons."""

    return len(text)


def build_safe_prompt(question: str, passages: list[RetrievedPassage]) -> str:
    """Construct a prompt with clear separators around untrusted user/context text."""

    context = "\n\n".join(
        f"[{passage.document.id}] {passage.document.title}\n{passage.document.text}"
        for passage in passages
    )
    return (
        "Instructions:\n"
        "Answer the user question using only the retrieved context. Cite document ids when useful.\n\n"
        "Retrieved context:\n"
        "---BEGIN CONTEXT---\n"
        f"{context}\n"
        "---END CONTEXT---\n\n"
        "User question:\n"
        "---BEGIN USER QUESTION---\n"
        f"{question}\n"
        "---END USER QUESTION---"
    )


def contains_evidence(answer: str, passages: list[RetrievedPassage]) -> bool:
    """Check whether the answer references selected document ids or distinctive terms."""

    lowered = answer.lower()
    return any(
        passage.document.id.lower() in lowered
        or any(term.lower() in lowered for term in passage.document.title.split()[:2])
        for passage in passages
    )

