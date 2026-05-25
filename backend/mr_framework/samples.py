"""Load data/test samples (C, T, D)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

from .models import SampleMeta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_TEST = PROJECT_ROOT / "data" / "test"

LIBRARIES = ("mui-material", "ant-design", "element-plus", "heroui", "mui-base-ui")
CATEGORIES = ("Inputs", "Data display", "Feedback", "Navigation", "Layout")


def parse_sample_dir_name(name: str) -> SampleMeta | None:
    m = re.match(r"^(\d+)-(.+)$", name)
    if not m:
        return None
    numeric_id = int(m.group(1))
    rest = m.group(2)
    library = None
    for lib in sorted(LIBRARIES, key=len, reverse=True):
        if rest.startswith(f"{lib}-"):
            library = lib
            rest = rest[len(lib) + 1 :]
            break
    if not library:
        return None
    for cat in sorted(CATEGORIES, key=len, reverse=True):
        if rest.startswith(f"{cat}-"):
            component_name = rest[len(cat) + 1 :]
            base = DATA_TEST / name
            return SampleMeta(
                sample_id=name,
                numeric_id=numeric_id,
                library=library,
                category=cat,
                component_name=component_name,
                sample_dir=str(base),
                source_path=str(base / "source.js"),
                test_path=str(base / "test.js"),
                description_path=str(base / "description.txt"),
            )
    return None


def list_sample_metas(
    *,
    library: str | None = None,
    category: str | None = None,
    sample_id: str | None = None,
) -> list[SampleMeta]:
    """All matching samples in stable sorted order (before offset/limit/shard)."""
    if sample_id:
        meta = parse_sample_dir_name(sample_id)
        return [meta] if meta else []
    if not DATA_TEST.is_dir():
        return []
    out: list[SampleMeta] = []
    for d in sorted(DATA_TEST.iterdir()):
        if not d.is_dir():
            continue
        meta = parse_sample_dir_name(d.name)
        if not meta:
            continue
        if library and meta.library != library:
            continue
        if category and meta.category != category:
            continue
        out.append(meta)
    return out


def shard_bounds(total: int, shard_index: int, num_shards: int) -> tuple[int, int]:
    """1-based shard_index; returns [start, end) slice indices."""
    if num_shards < 1:
        raise ValueError("num_shards must be >= 1")
    if not 1 <= shard_index <= num_shards:
        raise ValueError(f"shard_index must be 1..{num_shards}, got {shard_index}")
    start = (shard_index - 1) * total // num_shards
    end = shard_index * total // num_shards
    return start, end


def describe_shards(total: int, num_shards: int) -> list[dict[str, int | str]]:
    """Human-readable plan for splitting *total* samples into *num_shards* runs."""
    plan: list[dict[str, int | str]] = []
    for k in range(1, num_shards + 1):
        start, end = shard_bounds(total, k, num_shards)
        plan.append({
            "shard_index": k,
            "num_shards": num_shards,
            "start_index": start,
            "end_index": end,
            "count": end - start,
            "cli": f"--shard-index {k} --num-shards {num_shards}",
        })
    return plan


def iter_samples(
    *,
    library: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    shard_index: int | None = None,
    num_shards: int | None = None,
    sample_id: str | None = None,
) -> Iterator[SampleMeta]:
    if sample_id:
        meta = parse_sample_dir_name(sample_id)
        if meta:
            yield meta
        return

    metas = list_sample_metas(library=library, category=category)
    if shard_index is not None or num_shards is not None:
        if shard_index is None or num_shards is None:
            raise ValueError("shard_index and num_shards must be used together")
        start, end = shard_bounds(len(metas), shard_index, num_shards)
        metas = metas[start:end]

    if offset:
        metas = metas[offset:]
    n = 0
    for meta in metas:
        yield meta
        n += 1
        if limit is not None and n >= limit:
            break


def read_sample_files(meta: SampleMeta) -> tuple[str, str, str]:
    def _read(p: str) -> str:
        path = Path(p)
        return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""

    return _read(meta.source_path), _read(meta.test_path), _read(meta.description_path)


def component_name_variants(name: str) -> list[str]:
    variants = {name, name.strip(), name.replace(" ", ""), name.replace(" ", "-")}
    parts = re.split(r"[\s_-]+", name.strip())
    if parts:
        variants.add("".join(p.capitalize() for p in parts if p))
    return [v for v in variants if v]
