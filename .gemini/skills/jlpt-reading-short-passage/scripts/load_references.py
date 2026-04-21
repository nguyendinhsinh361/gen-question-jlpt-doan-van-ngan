#!/usr/bin/env python3
"""
load_references.py — Load & pretty-print sample JSON của "đoạn văn ngắn" cho AI agent.

Đọc các file `data/doan_van_ngan_n{1-5}_clean.json` (ở project root) và in ra:
  - Stats tổng quan (count, min/max/p25/p50/p75/avg jp_char_count)
  - Random samples theo level (để gen agent calibrate style, độ dài, question pattern)
  - 1 sample cụ thể theo id

Usage
-----
# Stats tất cả levels
python3 load_references.py --stats

# 3 random samples N3
python3 load_references.py --level N3 --count 3

# Specific sample theo id
python3 load_references.py --level N3 --id 143

# Seed để reproducible picks
python3 load_references.py --level N2 --count 5 --seed 42

# Tìm data file ở path khác
python3 load_references.py --data-dir /some/other/data --stats
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
from pathlib import Path


LEVELS = ["N1", "N2", "N3", "N4", "N5"]


def default_data_dir() -> str:
    """Thư mục chứa `doan_van_ngan_n{1-5}_clean.json`.

    Thứ tự ưu tiên:
      1. `<project-root>/data/` — project root = 4 cấp trên file này (`.claude/skills/<skill>/scripts/`).
      2. `./data/` ở CWD.
    """
    script_dir = Path(__file__).resolve().parent
    # scripts → skill-name → skills → .claude → project root
    project_root = script_dir.parent.parent.parent.parent
    candidate = project_root / "data"
    if candidate.exists():
        return str(candidate)
    return str(Path.cwd() / "data")


def data_path(data_dir: str, level: str) -> str:
    n = level.lower()  # N3 → n3
    return os.path.join(data_dir, f"doan_van_ngan_{n}_clean.json")


def load_level(data_dir: str, level: str) -> list[dict]:
    path = data_path(data_dir, level)
    if not os.path.exists(path):
        print(f"  [warn] Missing file: {path}", file=sys.stderr)
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"  [warn] {path} root is not a list", file=sys.stderr)
        return []
    return data


def percentile(values: list[int], pct: float) -> int:
    """Simple percentile (linear interpolation, pct ∈ [0, 100])."""
    if not values:
        return 0
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100.0)
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    if lo == hi:
        return s[lo]
    return int(round(s[lo] + (s[hi] - s[lo]) * (k - lo)))


def print_stats(data_dir: str) -> None:
    print(f"Data dir: {data_dir}\n")
    header = f"{'Level':<6}{'Count':>7}{'Min':>7}{'P25':>7}{'P50':>7}{'P75':>7}{'Avg':>7}{'Max':>7}"
    print(header)
    print("-" * len(header))
    for level in LEVELS:
        samples = load_level(data_dir, level)
        counts = [int(s.get("jp_char_count", 0) or 0) for s in samples]
        counts = [c for c in counts if c > 0]
        if not counts:
            print(f"{level:<6}{'0':>7}{'-':>7}{'-':>7}{'-':>7}{'-':>7}{'-':>7}{'-':>7}")
            continue
        print(
            f"{level:<6}"
            f"{len(samples):>7}"
            f"{min(counts):>7}"
            f"{percentile(counts, 25):>7}"
            f"{percentile(counts, 50):>7}"
            f"{percentile(counts, 75):>7}"
            f"{int(statistics.mean(counts)):>7}"
            f"{max(counts):>7}"
        )
    print()
    print("Target ranges (từ SKILL.md):")
    print("  N1: 220-260  |  N2: 240-290  |  N3: 220-290  |  N4: 180-240  |  N5: 100-160")


def format_sample(sample: dict) -> str:
    lines = []
    sid = sample.get("id")
    chars = sample.get("jp_char_count")
    kind = sample.get("kind", "?")
    level = sample.get("level", "?")
    lines.append(f"── Sample id={sid} | level=N{level} | kind={kind} | chars={chars} ──")
    txt = sample.get("general_text_read", "")
    lines.append(f"\n[general_text_read]")
    lines.append(txt)
    content = sample.get("content", []) or []
    for i, q in enumerate(content, 1):
        lines.append(f"\n[Q{i}] {q.get('question','')}")
        answers = q.get("answers", []) or []
        correct = q.get("correctAnswer", None)  # 0-based in source!
        for j, a in enumerate(answers):
            mark = "  ✅" if correct == j else "   "
            lines.append(f"  {j+1}.{mark} {a}")
        if correct is not None:
            lines.append(f"  → correctAnswer (source, 0-based) = {correct}  ⇒ CSV correct_answer = {correct + 1}")
    return "\n".join(lines) + "\n"


def pick_samples(data_dir: str, level: str, count: int, seed: int | None) -> list[dict]:
    samples = load_level(data_dir, level)
    if not samples:
        return []
    rng = random.Random(seed)
    k = min(count, len(samples))
    return rng.sample(samples, k)


def pick_by_id(data_dir: str, level: str, sid: int) -> dict | None:
    samples = load_level(data_dir, level)
    for s in samples:
        if s.get("id") == sid:
            return s
    return None


def main():
    ap = argparse.ArgumentParser(description="Load JLPT đoạn văn ngắn reference samples.")
    ap.add_argument("--data-dir", default=default_data_dir(),
                    help="Thư mục chứa data JSON (default: auto-detect <project-root>/data)")
    ap.add_argument("--stats", action="store_true", help="In stats per level")
    ap.add_argument("--level", choices=LEVELS, help="Level to load (N1..N5)")
    ap.add_argument("--count", type=int, default=2, help="Số sample random (default 2)")
    ap.add_argument("--id", type=int, help="Cụ thể id của sample")
    ap.add_argument("--seed", type=int, help="Random seed (reproducible)")

    args = ap.parse_args()

    if args.stats:
        print_stats(args.data_dir)
        return

    if not args.level:
        print("Cần --level hoặc --stats.", file=sys.stderr)
        ap.print_help()
        sys.exit(2)

    if args.id is not None:
        sample = pick_by_id(args.data_dir, args.level, args.id)
        if sample is None:
            print(f"Không tìm thấy sample id={args.id} trong {args.level}.", file=sys.stderr)
            sys.exit(1)
        print(format_sample(sample))
        return

    samples = pick_samples(args.data_dir, args.level, args.count, args.seed)
    if not samples:
        print(f"Không có sample ở {args.level}.", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(samples)} random sample(s) from {args.level} (seed={args.seed}):\n")
    for s in samples:
        print(format_sample(s))


if __name__ == "__main__":
    main()
