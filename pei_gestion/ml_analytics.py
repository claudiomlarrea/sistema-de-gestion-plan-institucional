"""Modelos exploratorios: series temporales, clustering supervisado opcional (RF), polaridad léxica simple."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    _HAS_SK = True
except ImportError:
    _HAS_SK = False

# Léxico mínimo en español (exploratorio; no sustituye modelos entrenados para producción).
_POS = {
    "logro",
    "mejora",
    "fortalecimiento",
    "éxito",
    "avance",
    "consolidación",
    "participación",
    "calidad",
    "impacto",
    "innovación",
}
_NEG = {
    "dificultad",
    "retraso",
    "demora",
    "problema",
    "falta",
    "ausencia",
    "obstáculo",
    "crítico",
    "insuficiente",
}


def simple_lexicon_polarity(text: str) -> float:
    words = str(text).lower().replace(",", " ").split()
    if not words:
        return 0.0
    score = 0
    for w in words:
        w2 = "".join(ch for ch in w if ch.isalnum() or ch in "áéíóúñ")
        if w2 in _POS:
            score += 1
        if w2 in _NEG:
            score -= 1
    return float(score) / max(len(words), 1)


def add_polarity_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    blob = out.apply(
        lambda r: " ".join(str(r.get(c, "")) for c in ("actividad", "detalle", "resultado")), axis=1
    )
    out["polaridad_lexica"] = blob.map(simple_lexicon_polarity)
    return out


def activities_by_period(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Serie temporal por semana (W) o mes (M) usando fecha_carga."""
    d = df.copy()
    d["fecha_carga"] = pd.to_datetime(d["fecha_carga"], errors="coerce")
    d = d.dropna(subset=["fecha_carga"])
    d = d.set_index("fecha_carga")
    s = d.groupby(pd.Grouper(freq=freq)).size().reset_index(name="n_actividades")
    return s


def rf_og_from_text_baseline(df: pd.DataFrame, random_state: int = 42) -> dict[str, Any]:
    """Baseline técnico: predecir OG desde texto (exploratorio, no evaluación de desempeño)."""
    if not _HAS_SK or len(df) < 40:
        return {"error": "Se requiere scikit-learn y al menos 40 filas."}
    corpus = df.apply(
        lambda r: " ".join(str(r.get(c, "")) for c in ("actividad", "detalle", "resultado")), axis=1
    )
    y = df["og"].astype(int)
    vec = TfidfVectorizer(max_features=800, ngram_range=(1, 2), min_df=2)
    X = vec.fit_transform(corpus)
    counts = y.value_counts()
    strat = y if counts.min() >= 2 and len(counts) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=strat
    )
    clf = RandomForestClassifier(n_estimators=60, max_depth=12, random_state=random_state, class_weight="balanced")
    clf.fit(X_train, y_train)
    acc = float(clf.score(X_test, y_test))
    report = classification_report(y_test, clf.predict(X_test), zero_division=0)
    return {
        "accuracy_holdout": acc,
        "classification_report": report,
        "feature_model": "TF-IDF + RandomForest",
        "random_state": random_state,
        "disclaimer": "Uso exclusivamente exploratorio; no evalúa desempeño de personas ni cumplimiento institucional.",
    }
