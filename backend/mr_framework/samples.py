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


def iter_samples(
    *,
    library: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    sample_id: str | None = None,
) -> Iterator[SampleMeta]:
    if sample_id:
        meta = parse_sample_dir_name(sample_id)
        if meta:
            yield meta
        return
    n = 0
    if not DATA_TEST.is_dir():
        return
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
