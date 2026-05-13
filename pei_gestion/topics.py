"""Temas emergentes (NMF) y clustering sobre textos — comparte motor con analítica."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd

try:
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.decomposition import NMF
    from sklearn.feature_extraction.text import TfidfVectorizer

    _HAS_SK = True
except ImportError:
    _HAS_SK = False


@dataclass
class TopicModelResult:
    feature_names: list[str]
    topics: list[list[tuple[str, float]]]
    doc_topic: np.ndarray
    model_version: str


def build_corpus(df: pd.DataFrame) -> list[str]:
    parts = []
    for _, r in df.iterrows():
        parts.append(
            " ".join(
                str(r.get(c, ""))
                for c in ("actividad", "detalle", "resultado")
                if pd.notna(r.get(c))
            )
        )
    return parts


def run_nmf_topics(
    df: pd.DataFrame,
    n_topics: int = 8,
    max_features: int = 2000,
    random_state: int = 42,
) -> TopicModelResult:
    if not _HAS_SK:
        raise RuntimeError("scikit-learn es requerido para temas NMF")
    corpus = build_corpus(df)
    vec = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2), min_df=2)
    X = vec.fit_transform(corpus)
    nmf = NMF(n_components=n_topics, random_state=random_state, init="nndsvda", max_iter=200)
    W = nmf.fit_transform(X)
    H = nmf.components_
    names = vec.get_feature_names_out()
    topics: list[list[tuple[str, float]]] = []
    for ti in range(n_topics):
        top = np.argsort(H[ti])[-12:][::-1]
        topics.append([(str(names[i]), float(H[ti, i])) for i in top])
    return TopicModelResult(
        feature_names=list(names),
        topics=topics,
        doc_topic=W,
        model_version="sklearn_NMF+TF-IDF",
    )


def run_kmeans_on_tfidf(
    df: pd.DataFrame,
    n_clusters: int = 6,
    max_features: int = 1500,
    random_state: int = 42,
) -> tuple[np.ndarray, TfidfVectorizer]:
    if not _HAS_SK:
        raise RuntimeError("scikit-learn es requerido para clustering")
    corpus = build_corpus(df)
    vec = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2), min_df=2)
    X = vec.fit_transform(corpus)
    km = MiniBatchKMeans(n_clusters=n_clusters, random_state=random_state, batch_size=256, n_init=10)
    labels = km.fit_predict(X)
    return labels, vec


def try_sentence_embedding_cluster(
    df: pd.DataFrame, n_clusters: int = 6, random_state: int = 42
) -> Optional[tuple[np.ndarray, str]]:
    """Opcional: sentence-transformers si está instalado."""
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import MiniBatchKMeans
    except ImportError:
        return None
    corpus = build_corpus(df)
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    emb = model.encode(corpus, show_progress_bar=False)
    km = MiniBatchKMeans(n_clusters=n_clusters, random_state=random_state, batch_size=256, n_init=10)
    labels = km.fit_predict(emb)
    return labels, "sentence-transformers MiniLM + MiniBatchKMeans"
