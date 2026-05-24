"""Logical data models for reports and pipeline I/O."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class SampleMeta:
    sample_id: str
    numeric_id: int
    library: str
    category: str
    component_name: str
    sample_dir: str
    source_path: str
    test_path: str

    @property
    def scenario(self) -> str:
        return (
            f"组件库 / {self.component_name} 组件 "
            f"({self.library} · {self.category})"
        )


@dataclass
class MetamorphicRelation:
    id: str
    component: str
    relation_type: str
    type_category: str
    description: str
    expected_relation: str
    confidence: float = 0.6
    source: str = "llm"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompletenessMetrics:
    total_mrs: int = 0
    touched_mrs: int = 0
    covered_mrs: int = 0
    touch_rate: float = 0.0
    coverage_rate: float = 0.0
    hybrid_touched_mrs: int = 0
    hybrid_touch_rate: float = 0.0
    missed_touch_uncovered: int = 0
    touched_not_covered: int = 0
    touched_not_covered_rate: float = 0.0
    overlooked_uncovered_rate: float = 0.0
    distinct_relation_types: int = 0
    covered_relation_types: int = 0
    relation_type_coverage_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BlindSpotStats:
    miss_at_uncov: int = 0
    touched_not_covered: int = 0
    top_blind_mr_types: list[dict[str, Any]] = field(default_factory=list)
    by_type_category: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TestPriority:
    library: str
    component_name: str
    category: str
    relation_type: str
    type_category: str
    reason: str
    priority_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AlignmentReport:
    version_snapshot: str
    exp1: dict[str, Any] = field(default_factory=dict)
    exp2: dict[str, Any] = field(default_factory=dict)
    val_summary: str = ""
    methodology_note: str = (
        "RQ3 uses cross-sectional alignment/co-occurrence between open bug pressure "
        "and MR completeness gaps — not predictive causation."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SampleReport:
    meta: SampleMeta
    version_snapshot: str
    model: str
    metamorphic_relations: list[dict[str, Any]]
    mr_coverage: list[dict[str, Any]]
    completeness: dict[str, Any]
    blind_spots: dict[str, Any]
    test_priorities: list[dict[str, Any]]
    issue_pressure: int = 0
    alignment_notes: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": asdict(self.meta),
            "version_snapshot": self.version_snapshot,
            "model": self.model,
            "provenance": self.provenance,
            "metamorphic_relations": self.metamorphic_relations,
            "mr_coverage": self.mr_coverage,
            "completeness": self.completeness,
            "blind_spots": self.blind_spots,
            "test_priorities": self.test_priorities,
            "issue_pressure": self.issue_pressure,
            "alignment_notes": self.alignment_notes,
            "generated_at": self.generated_at,
        }
