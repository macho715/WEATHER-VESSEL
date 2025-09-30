"""ERI 규칙 로더. ERI rules loader."""

from __future__ import annotations

from pathlib import Path
from typing import IO, Any, Iterable

import yaml  # type: ignore[import-untyped]

from wv.core.models import LogiBaseModel

from ..core.schema import MarineVariable


class ThresholdRule(LogiBaseModel):
    """ERI 임계 규칙. ERI threshold rule."""

    variable: MarineVariable
    caution: float
    danger: float
    weight: float
    direction: str = "max"


class ERIRuleSet(LogiBaseModel):
    """ERI 규칙 세트. ERI rule set."""

    base_score: float
    caution_penalty: float
    danger_penalty: float
    rules: tuple[ThresholdRule, ...]


def _iter_rules(data: Iterable[dict[str, Any]]) -> list[ThresholdRule]:
    rules: list[ThresholdRule] = []
    for item in data:
        rules.append(
            ThresholdRule(
                variable=MarineVariable(item["variable"]),
                caution=float(item["caution"]),
                danger=float(item["danger"]),
                weight=float(item["weight"]),
                direction=item.get("direction", "max"),
            )
        )
    return rules


def load_rule_set(resource: str | Path | IO[str]) -> ERIRuleSet:
    """YAML/TOML 규칙 로드. Load ERI rules from YAML/TOML."""

    if hasattr(resource, "read"):
        raw = yaml.safe_load(resource)
    else:
        path = Path(resource)
        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    rules = _iter_rules(raw["rules"])
    return ERIRuleSet(
        base_score=float(raw["base_score"]),
        caution_penalty=float(raw["caution_penalty"]),
        danger_penalty=float(raw["danger_penalty"]),
        rules=tuple(rules),
    )
