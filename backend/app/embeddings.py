from __future__ import annotations

import hashlib
import math
import os
import re
from abc import ABC, abstractmethod


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
DEFAULT_EMBEDDING_DIMENSION = 384


class EmbeddingProvider(ABC):
    dimension: int

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


class DeterministicHashEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> None:
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = TOKEN_PATTERN.findall(text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 6) for value in vector]


class SentenceTransformersEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in embedding] for embedding in embeddings]


def build_embedding_provider() -> EmbeddingProvider:
    provider = os.getenv("EMBEDDING_PROVIDER", "hash").lower()
    if provider == "sentence_transformers":
        return SentenceTransformersEmbeddingProvider(
            model_name=os.getenv(
                "SENTENCE_TRANSFORMERS_MODEL",
                "sentence-transformers/all-MiniLM-L6-v2",
            )
        )
    return DeterministicHashEmbeddingProvider()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
