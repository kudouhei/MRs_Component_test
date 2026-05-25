"""Data models."""

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
    description_path: str

    @property
    def scenario(self) -> str:
        return f"{self.library} / {self.category} / {self.component_name}"


@dataclass
class MetamorphicRelation:
    id: str
    component: str
    relation_type: str
    type_category: str
    description: str
    expected_relation: str
    confidence: float = 0.7
    source: str = "llm"
    category_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SampleReport:
    meta: SampleMeta
    version_snapshot: str
    metamorphic_relations: list[dict[str, Any]]
    mr_coverage: list[dict[str, Any]]
    completeness: dict[str, Any]
    blind_spots: dict[str, Any]
    test_priorities: list[dict[str, Any]]
    improvement_suggestions: list[dict[str, Any]] = field(default_factory=list)
    issue_pressure: int = 0
    alignment_notes: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": asdict(self.meta),
            "version_snapshot": self.version_snapshot,
            "metamorphic_relations": self.metamorphic_relations,
            "mr_coverage": self.mr_coverage,
            "completeness": self.completeness,
            "blind_spots": self.blind_spots,
            "test_priorities": self.test_priorities,
            "improvement_suggestions": self.improvement_suggestions,
            "issue_pressure": self.issue_pressure,
            "alignment_notes": self.alignment_notes,
            "provenance": self.provenance,
            "generated_at": self.generated_at,
        }


@dataclass
class AlignmentReport:
    version_snapshot: str
    exp1: dict[str, Any] = field(default_factory=dict)
    exp2: dict[str, Any] = field(default_factory=dict)
    val_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
