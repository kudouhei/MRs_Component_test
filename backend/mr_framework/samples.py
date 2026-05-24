"""Discover and parse data/test samples."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

from .models import SampleMeta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_TEST = PROJECT_ROOT / "data" / "test"

LIBRARIES = (
    "mui-material",
    "ant-design",
    "element-plus",
    "heroui",
    "mui-base-ui",
)

CATEGORIES = (
    "Inputs",
    "Data display",
    "Feedback",
    "Navigation",
    "Layout",
)


def parse_sample_dir_name(name: str) -> SampleMeta | None:
    m = re.match(r"^(\d+)-(.+)$", name)
    if not m:
        return None
    numeric_id = int(m.group(1))
    rest = m.group(2)
    library = None
    for lib in sorted(LIBRARIES, key=len, reverse=True):
        prefix = f"{lib}-"
        if rest.startswith(prefix):
            library = lib
            rest = rest[len(prefix) :]
            break
    if not library:
        return None
    category = None
    for cat in sorted(CATEGORIES, key=len, reverse=True):
        prefix = f"{cat}-"
        if rest.startswith(prefix):
            category = cat
            component_name = rest[len(prefix) :]
            break
    else:
        return None
    return SampleMeta(
        sample_id=name,
        numeric_id=numeric_id,
        library=library,
        category=category,
        component_name=component_name,
        sample_dir=str(DATA_TEST / name),
        source_path=str(DATA_TEST / name / "source.js"),
        test_path=str(DATA_TEST / name / "test.js"),
    )


def iter_samples(
    *,
    library: str | None = None,
    limit: int | None = None,
    sample_id: str | None = None,
) -> Iterator[SampleMeta]:
    if sample_id:
        meta = parse_sample_dir_name(sample_id)
        if meta:
            yield meta
        return
    count = 0
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
        yield meta
        count += 1
        if limit is not None and count >= limit:
            break


def read_sample_files(meta: SampleMeta) -> tuple[str, str]:
    src = Path(meta.source_path)
    tst = Path(meta.test_path)
    code = src.read_text(encoding="utf-8", errors="replace") if src.exists() else ""
    tests = tst.read_text(encoding="utf-8", errors="replace") if tst.exists() else ""
    return code, tests


def component_name_variants(name: str) -> list[str]:
    variants = {name, name.strip(), name.replace(" ", ""), name.replace(" ", "-")}
    parts = re.split(r"[\s_-]+", name.strip())
    if parts:
        variants.add("".join(p.capitalize() for p in parts if p))
    return [v for v in variants if v]
