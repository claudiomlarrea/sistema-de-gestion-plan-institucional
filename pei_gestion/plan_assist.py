"""Borradores de planeación asistida: export YAML sin pisar el plan oficial."""
from __future__ import annotations

import datetime as dt
from typing import Any

import yaml


def build_proposals_document(
    plan_id: str,
    *,
    sugerencias: list[str],
    objetivos_nuevos: list[dict[str, Any]],
    referencia_clusters: str = "",
    autor: str = "usuario_app",
) -> dict[str, Any]:
    return {
        "plan_id": plan_id,
        "tipo": "plan_proposals_borrador",
        "generado": dt.datetime.now().isoformat(timespec="seconds"),
        "autor": autor,
        "sugerencias_texto": sugerencias,
        "objetivos_nuevos": objetivos_nuevos,
        "referencia_semantica": referencia_clusters,
        "governance": "No reemplaza el PEI aprobado; requiere resolución institucional antes de pasar a oficial.",
    }


def proposals_to_yaml(doc: dict[str, Any]) -> str:
    return yaml.dump(doc, allow_unicode=True, sort_keys=False, width=110)
