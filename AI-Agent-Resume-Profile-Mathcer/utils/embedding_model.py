import os
from typing import List, Optional

import numpy as np

from utils.logger import get_logger


logger = get_logger("embedding_model")


class EmbeddingModel:
    def __init__(self) -> None:
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self._model = None
        self._enabled = False

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._model = SentenceTransformer(self.model_name)
            self._enabled = True
            logger.info("Embedding model loaded: %s", self.model_name)
        except Exception as exc:
            logger.info("Embedding model unavailable, falling back to TF-IDF only: %s", exc)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._model is not None

    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        if not self.enabled or not texts:
            return None

        try:
            embeddings = self._model.encode(  # type: ignore[union-attr]
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return np.asarray(embeddings, dtype=np.float32)
        except Exception as exc:
            logger.info("Embedding encode failed, disabling embedding model: %s", exc)
            self._enabled = False
            return None
