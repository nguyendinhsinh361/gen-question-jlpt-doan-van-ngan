#!/usr/bin/env python3
"""Automated furigana coverage checker.

For a given HTML file + passage level, this script:
1. Extracts every kanji character from the body text (skipping <rt> content)
2. Identifies kanji INSIDE <ruby> tags vs OUTSIDE
3. Looks up each kanji's JLPT level in kanji_jlpt_sensei.csv
4. Reports MISSING_FURIGANA: kanji above passage level that are NOT inside <ruby>
5. Optionally reports REDUNDANT_FURIGANA: kanji at/below level inside <ruby>

Exits with code 1 if any MISSING furigana detected.

Usage:
    python3 check_furigana.py --file path/to/passage.html --level N3 --csv path/to/kanji_jlpt_sensei.csv
    python3 check_furigana.py --html-dir path/to/dir --level-from-filename --csv path/to/kanji_jlpt_sensei.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# JLPT level ordering (N5 = easiest, N1 = hardest).
# A kanji at level X is "above" a passage of level Y if X is harder (lower number).
LEVEL_RANK = {"N5": 5, "N4": 4, "N3": 3, "N2": 2, "N1": 1}

# Kanji unicode ranges
KANJI_RE = re.compile(r"[一-鿿㐀-䶿]")

# Find <ruby>...</ruby> blocks
RUBY_BLOCK = re.compile(r"<ruby[^>]*>(.*?)</ruby>", re.DOTALL)

# Strip <rt>...</rt> content (furigana reading) from anything
RT_STRIP = re.compile(r"<rt[^>]*>.*?</rt>", re.DOTALL)

# Strip HTML tags entirely (for getting plain text)
TAG_STRIP = re.compile(r"<[^>]+>")


def load_kanji_levels(csv_path: Path) -> dict[str, str]:
    """Return {kanji_char: 'N1'|'N2'|'N3'|'N4'|'N5'} from CSV."""
    mapping: dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kanji = (row.get("kanji") or "").strip()
            jlpt = (row.get("jlpt") or "").strip().upper()
            # Only accept single-char kanji entries with valid JLPT level
            if len(kanji) == 1 and KANJI_RE.match(kanji) and jlpt in LEVEL_RANK:
                # If duplicates exist, keep the easier (higher rank = lower difficulty) — be conservative
                if kanji in mapping:
                    if LEVEL_RANK[jlpt] > LEVEL_RANK[mapping[kanji]]:
                        mapping[kanji] = jlpt
                else:
                    mapping[kanji] = jlpt
    return mapping


def extract_body(html: str) -> str:
    """Extract main passage body. Skip <head>, <style>, <script>."""
    # Remove script/style/head
    html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Try to find .passage div, otherwise <body>
    m = re.search(r'<div[^>]*class=[\'"][^\'"]*\bpassage\b[^\'"]*[\'"][^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    return html


def find_ruby_kanji_set(body: str) -> set[str]:
    """Return set of kanji chars that appear INSIDE <ruby>...</ruby> blocks."""
    result: set[str] = set()
    for m in RUBY_BLOCK.finditer(body):
        inner = m.group(1)
        # Strip <rt>...</rt>
        inner = RT_STRIP.sub("", inner)
        # Strip remaining tags
        inner = TAG_STRIP.sub("", inner)
        for ch in inner:
            if KANJI_RE.match(ch):
                result.add(ch)
    return result


def extract_outside_ruby_kanji(body: str) -> list[tuple[str, int]]:
    """Return list of (kanji, char_index) for kanji OUTSIDE <ruby> blocks.

    Index is approximate (position in plain text after stripping tags/ruby).
    """
    # Replace <ruby>...</ruby> blocks with placeholder so we count outside-ruby kanji
    placeholder = " "  # NUL placeholder
    masked = RUBY_BLOCK.sub(placeholder, body)
    # Strip remaining tags
    plain = TAG_STRIP.sub("", masked)

    result: list[tuple[str, int]] = []
    for i, ch in enumerate(plain):
        if KANJI_RE.match(ch):
            result.append((ch, i))
    return result



# Pattern: kanji DIRECTLY adjacent to <ruby> block (no separator)
# Matches: kanji<ruby>...</ruby> or <ruby>...</ruby>kanji
PARTIAL_BEFORE = re.compile(r"([一-鿿])\s*(<ruby[^>]*>[^<]*<rt[^>]*>[^<]*</rt>\s*</ruby>)")
PARTIAL_AFTER = re.compile(r"(<ruby[^>]*>[^<]*<rt[^>]*>[^<]*</rt>\s*</ruby>)\s*([一-鿿])")


def find_partial_word_ruby(body: str) -> list[str]:
    """Find kanji adjacent to ruby block — likely partial-word ruby (Quy tắc B violation).

    Returns list of context snippets showing the partial-word issue.
    """
    snippets: list[str] = []
    for m in PARTIAL_BEFORE.finditer(body):
        kanji = m.group(1)
        ruby = m.group(2)
        snippets.append(f"{kanji}{ruby}")
    for m in PARTIAL_AFTER.finditer(body):
        ruby = m.group(1)
        kanji = m.group(2)
        snippets.append(f"{ruby}{kanji}")
    return snippets


def check_furigana(
    html: str,
    passage_level: str,
    kanji_levels: dict[str, str],
) -> dict:
    """Return dict with: missing (list), redundant (list), summary."""
    body = extract_body(html)

    ruby_kanji = find_ruby_kanji_set(body)
    outside_kanji = extract_outside_ruby_kanji(body)

    passage_rank = LEVEL_RANK[passage_level]

    missing: dict[str, int] = {}  # kanji → count of occurrences outside ruby
    redundant: set[str] = set()   # kanji inside ruby that's at/below level
    unknown: dict[str, int] = {}  # kanji not in CSV — agent must decide

    for kanji, _idx in outside_kanji:
        klevel = kanji_levels.get(kanji)
        if not klevel:
            unknown[kanji] = unknown.get(kanji, 0) + 1
            continue
        krank = LEVEL_RANK[klevel]
        if krank < passage_rank:
            # Kanji is HARDER than passage level → SHOULD have furigana but doesn't
            missing[kanji] = missing.get(kanji, 0) + 1

    for kanji in ruby_kanji:
        klevel = kanji_levels.get(kanji)
        if not klevel:
            continue
        krank = LEVEL_RANK[klevel]
        if krank >= passage_rank:
            # Kanji is at/easier than passage level → furigana might be redundant
            redundant.add(kanji)

    partial_word_ruby = find_partial_word_ruby(body)

    return {
        "missing": missing,
        "redundant": sorted(redundant),
        "unknown": unknown,
        "partial_word_ruby": partial_word_ruby,
        "passage_level": passage_level,
        "ruby_kanji_count": len(ruby_kanji),
        "outside_kanji_count": len(outside_kanji),
    }


def format_report(file_path: Path, result: dict) -> tuple[str, bool]:
    """Format human-readable report. Returns (text, has_errors)."""
    lines = []
    has_error = False

    lvl = result["passage_level"]
    lines.append(f"File: {file_path.name} | Level: {lvl}")
    lines.append(f"  Ruby kanji: {result['ruby_kanji_count']} unique | Outside-ruby kanji: {result['outside_kanji_count']} total occurrences")

    missing = result["missing"]
    if missing:
        has_error = True
        lines.append(f"\n  MISSING FURIGANA — {len(missing)} unique kanji ABOVE level {lvl} không có ruby:")
        for kanji, count in sorted(missing.items(), key=lambda x: -x[1]):
            klevel = "?"
            lines.append(f"    {kanji} (xuất hiện {count} lần) — phải có <ruby>{kanji}<rt>...</rt></ruby>")

    redundant = result["redundant"]
    if redundant:
        lines.append(f"\n  WARNING: REDUNDANT FURIGANA — {len(redundant)} kanji có ruby nhưng ≤ level {lvl}:")
        for kanji in redundant:
            lines.append(f"    {kanji} — ruby thừa, có thể bỏ")

    unknown = result["unknown"]
    if unknown:
        lines.append(f"\n  UNKNOWN KANJI (không có trong CSV) — {len(unknown)} unique:")
        for kanji, count in sorted(unknown.items(), key=lambda x: -x[1])[:20]:
            lines.append(f"    {kanji} (xuất hiện {count} lần) — agent quyết định cần ruby không (kanji hiếm/cổ → thường có)")

    partial = result.get("partial_word_ruby") or []
    if partial:
        has_error = True
        lines.append(f"\n  PARTIAL-WORD FURIGANA (Quy tắc B vi phạm) — {len(partial)} chỗ kanji liền kề ruby (rắc 1 phần từ thay vì cả từ):")
        for snippet in partial[:10]:
            lines.append(f"    {snippet}  →  PHẢI gộp cả từ thành 1 <ruby> bao trọn")
        if len(partial) > 10:
            lines.append(f"    ... và {len(partial) - 10} chỗ khác")

    if not missing and not redundant and not unknown:
        lines.append("\n  PASS — Furigana coverage OK")

    return "\n".join(lines), has_error


def extract_level_from_filename(filename: str) -> str | None:
    """Extract N1/N2/N3/N4/N5 from filename like 'N3_abc123.html'."""
    m = re.match(r"^(N[1-5])_", filename)
    if m:
        return m.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(description="Check furigana coverage against kanji_jlpt_sensei.csv")
    parser.add_argument("--file", help="Single HTML file")
    parser.add_argument("--html-dir", help="Directory of HTML files (uses filename for level)")
    parser.add_argument("--level", choices=list(LEVEL_RANK.keys()), help="Passage level (required for --file)")
    parser.add_argument("--csv", required=True, help="Path to kanji_jlpt_sensei.csv")
    parser.add_argument("--show-warnings", action="store_true", help="Also exit 1 if redundant furigana found")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    kanji_levels = load_kanji_levels(csv_path)
    print(f"Loaded {len(kanji_levels)} kanji entries from {csv_path.name}")

    files_to_check: list[tuple[Path, str]] = []

    if args.file:
        if not args.level:
            print("ERROR: --level required with --file", file=sys.stderr)
            return 2
        files_to_check.append((Path(args.file), args.level))
    elif args.html_dir:
        d = Path(args.html_dir)
        for html_file in sorted(d.glob("*.html")):
            level = extract_level_from_filename(html_file.name)
            if not level:
                print(f"WARN: skipping {html_file.name} — cannot detect level from filename")
                continue
            files_to_check.append((html_file, level))
    else:
        print("ERROR: must provide --file or --html-dir", file=sys.stderr)
        return 2

    total_errors = 0
    total_warnings = 0

    for path, level in files_to_check:
        html = path.read_text(encoding="utf-8")
        result = check_furigana(html, level, kanji_levels)
        report, has_error = format_report(path, result)
        print("\n" + report)
        if has_error:
            total_errors += 1
        if result["redundant"] or result["unknown"]:
            total_warnings += 1

    print(f"\n=== SUMMARY ===")
    print(f"Files checked: {len(files_to_check)}")
    print(f"Files with MISSING furigana: {total_errors}")
    print(f"Files with warnings (redundant/unknown): {total_warnings}")

    exit_code = 0
    if total_errors > 0:
        exit_code = 1
    if args.show_warnings and total_warnings > 0:
        exit_code = max(exit_code, 1)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
