#!/usr/bin/env python3
"""Automated furigana coverage checker — WORD-LEVEL (Quy tắc B).

Logic:
1. Identify compound words = consecutive runs of kanji characters
2. For each word OUTSIDE <ruby>: if ANY char ≥ above passage level → whole word MISSING_FURIGANA
3. For each word INSIDE <ruby>: if ALL chars are at/below passage level → REDUNDANT_FURIGANA
   (NOT redundant if word contains ≥1 above-level char — Quy tắc B exception)
4. PARTIAL_WORD: kanji adjacent to <ruby> block (rule B violation — splitting a word)

Usage:
    python3 check_furigana.py --file passage.html --level N3 --csv kanji_jlpt_sensei.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

LEVEL_RANK = {"N5": 5, "N4": 4, "N3": 3, "N2": 2, "N1": 1}
KANJI_RE = re.compile(r"[一-鿿㐀-䶿]")
KANJI_RUN_RE = re.compile(r"[一-鿿㐀-䶿]+")  # consecutive kanji run = compound word
RUBY_BLOCK = re.compile(r"<ruby[^>]*>(.*?)</ruby>", re.DOTALL)
RT_STRIP = re.compile(r"<rt[^>]*>.*?</rt>", re.DOTALL)
TAG_STRIP = re.compile(r"<[^>]+>")

# Partial-word patterns (raw kanji adjacent to ruby block)
PARTIAL_BEFORE = re.compile(r"([一-鿿])\s*(<ruby[^>]*>[^<]*<rt[^>]*>[^<]*</rt>\s*</ruby>)")
PARTIAL_AFTER = re.compile(r"(<ruby[^>]*>[^<]*<rt[^>]*>[^<]*</rt>\s*</ruby>)\s*([一-鿿])")


def load_kanji_levels(csv_path: Path) -> dict[str, str]:
    """Return {kanji_char: 'N1'..'N5'} from CSV."""
    mapping: dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kanji = (row.get("kanji") or "").strip()
            jlpt = (row.get("jlpt") or "").strip().upper()
            if len(kanji) == 1 and KANJI_RE.match(kanji) and jlpt in LEVEL_RANK:
                if kanji in mapping:
                    if LEVEL_RANK[jlpt] > LEVEL_RANK[mapping[kanji]]:
                        mapping[kanji] = jlpt
                else:
                    mapping[kanji] = jlpt
    return mapping


def extract_body(html: str) -> str:
    html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    m = re.search(r'<div[^>]*class=[\'"][^\'"]*\bpassage\b[^\'"]*[\'"][^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    return html


def extract_ruby_words(body: str) -> list[str]:
    """Return list of kanji compound words INSIDE <ruby> blocks."""
    words: list[str] = []
    for m in RUBY_BLOCK.finditer(body):
        inner = m.group(1)
        inner = RT_STRIP.sub("", inner)
        inner = TAG_STRIP.sub("", inner)
        # Extract all kanji runs from this ruby block
        for run in KANJI_RUN_RE.findall(inner):
            words.append(run)
    return words


def extract_outside_ruby_words(body: str) -> list[str]:
    """Return list of kanji compound words OUTSIDE <ruby> blocks."""
    # Mask out ruby blocks (replace with non-kanji placeholder)
    masked = RUBY_BLOCK.sub(" ", body)
    # Strip remaining HTML tags
    plain = TAG_STRIP.sub(" ", masked)
    # Find all consecutive kanji runs
    return KANJI_RUN_RE.findall(plain)


def find_partial_word_ruby(body: str) -> list[str]:
    snippets: list[str] = []
    for m in PARTIAL_BEFORE.finditer(body):
        snippets.append(f"{m.group(1)}{m.group(2)}")
    for m in PARTIAL_AFTER.finditer(body):
        snippets.append(f"{m.group(1)}{m.group(2)}")
    return snippets


def word_min_rank(word: str, kanji_levels: dict[str, str]) -> int | None:
    """Return min rank (= hardest level) of any kanji in word.
    
    Lower rank = harder (N1=1, N5=5).
    Returns None if no kanji has known level."""
    ranks = []
    for k in word:
        lvl = kanji_levels.get(k)
        if lvl:
            ranks.append(LEVEL_RANK[lvl])
    return min(ranks) if ranks else None


def check_furigana(html: str, passage_level: str, kanji_levels: dict[str, str]) -> dict:
    body = extract_body(html)
    passage_rank = LEVEL_RANK[passage_level]

    ruby_words = extract_ruby_words(body)
    outside_words = extract_outside_ruby_words(body)

    # MISSING: words outside ruby that contain ≥1 above-level kanji
    missing: dict[str, int] = {}  # word → count
    # REDUNDANT: words inside ruby where ALL chars are at/below level (no exception kanji)
    redundant_words: dict[str, int] = {}
    # UNKNOWN: words with kanji not in CSV
    unknown_words: dict[str, int] = {}

    for word in outside_words:
        # Has any kanji not in CSV?
        unknowns = [k for k in word if k not in kanji_levels]
        if unknowns:
            unknown_words[word] = unknown_words.get(word, 0) + 1
            # Continue to also check known kanji
        min_rank = word_min_rank(word, kanji_levels)
        if min_rank is not None and min_rank < passage_rank:
            # At least 1 kanji in word is harder than passage level → whole word should have ruby
            missing[word] = missing.get(word, 0) + 1

    for word in ruby_words:
        # All kanji at/below level (no exception)?
        min_rank = word_min_rank(word, kanji_levels)
        if min_rank is None:
            continue  # word has only unknown kanji — agent decides
        if min_rank >= passage_rank:
            # No char is harder than passage level → ruby is redundant
            redundant_words[word] = redundant_words.get(word, 0) + 1
        # else: word has at least 1 above-level char → ruby is CORRECT (Quy tắc B)

    partial_word_ruby = find_partial_word_ruby(body)

    return {
        "missing": missing,
        "redundant": redundant_words,
        "unknown": unknown_words,
        "partial_word_ruby": partial_word_ruby,
        "passage_level": passage_level,
        "ruby_words_count": len(ruby_words),
        "outside_words_count": len(outside_words),
    }


def format_report(file_path: Path, result: dict, kanji_levels: dict) -> tuple[str, bool]:
    lines = []
    has_error = False
    lvl = result["passage_level"]
    lines.append(f"File: {file_path.name} | Level: {lvl}")
    lines.append(f"  Words in ruby: {result['ruby_words_count']} | Words outside ruby: {result['outside_words_count']}")

    missing = result["missing"]
    if missing:
        has_error = True
        lines.append(f"\n  MISSING FURIGANA (Quy tắc B — word-level) — {len(missing)} từ chứa kanji ABOVE level {lvl}:")
        for word, count in sorted(missing.items(), key=lambda x: -x[1]):
            # Show per-char level breakdown
            chars_info = []
            for k in word:
                kl = kanji_levels.get(k, "?")
                marker = "*" if kl != "?" and LEVEL_RANK.get(kl, 99) < LEVEL_RANK[lvl] else ""
                chars_info.append(f"{k}{marker}={kl}")
            lines.append(f"    {word} (×{count}) [{', '.join(chars_info)}] — PHẢI có <ruby>{word}<rt>...</rt></ruby> (toàn từ)")
            lines.append(f"      (* = kanji vượt level → buộc cả từ phải có ruby theo Quy tắc B)")

    redundant = result["redundant"]
    if redundant:
        lines.append(f"\n  REDUNDANT FURIGANA — {len(redundant)} từ có ruby nhưng MỌI kanji ≤ level {lvl}:")
        for word, count in sorted(redundant.items(), key=lambda x: -x[1]):
            chars_info = ", ".join(f"{k}={kanji_levels.get(k, '?')}" for k in word)
            lines.append(f"    {word} (×{count}) [{chars_info}] — ruby thừa, có thể bỏ")

    unknown = result["unknown"]
    if unknown:
        lines.append(f"\n  UNKNOWN KANJI in words (không có trong CSV) — {len(unknown)}:")
        for word, count in sorted(unknown.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"    {word} (×{count}) — kanji hiếm, agent quyết định")

    partial = result.get("partial_word_ruby") or []
    if partial:
        has_error = True
        lines.append(f"\n  PARTIAL-WORD FURIGANA (Quy tắc B vi phạm) — {len(partial)} chỗ kanji liền kề ruby (rắc 1 phần từ):")
        for snippet in partial[:10]:
            lines.append(f"    {snippet}  →  PHẢI gộp cả từ thành 1 <ruby> bao trọn")

    if not missing and not redundant and not unknown and not partial:
        lines.append("\n  PASS — Furigana coverage OK (word-level)")

    return "\n".join(lines), has_error


def extract_level_from_filename(filename: str) -> str | None:
    m = re.match(r"^([nN][1-5])_", filename)
    return m.group(1).upper() if m else None


def main():
    parser = argparse.ArgumentParser(description="Check furigana coverage (word-level)")
    parser.add_argument("--file", help="Single HTML file")
    parser.add_argument("--html-dir", help="Directory of HTML files")
    parser.add_argument("--level", choices=list(LEVEL_RANK.keys()))
    parser.add_argument("--csv", required=True)
    parser.add_argument("--show-warnings", action="store_true")
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
                print(f"WARN: skipping {html_file.name}")
                continue
            files_to_check.append((html_file, level))
    else:
        print("ERROR: --file or --html-dir required", file=sys.stderr)
        return 2

    total_errors = 0
    total_warnings = 0
    for path, level in files_to_check:
        html = path.read_text(encoding="utf-8")
        result = check_furigana(html, level, kanji_levels)
        report, has_error = format_report(path, result, kanji_levels)
        print("\n" + report)
        if has_error:
            total_errors += 1
        if result["redundant"] or result["unknown"]:
            total_warnings += 1

    print(f"\n=== SUMMARY ===")
    print(f"Files checked: {len(files_to_check)}")
    print(f"Files with MISSING furigana (or PARTIAL): {total_errors}")
    print(f"Files with warnings (redundant/unknown): {total_warnings}")
    exit_code = 0
    if total_errors > 0:
        exit_code = 1
    if args.show_warnings and total_warnings > 0:
        exit_code = max(exit_code, 1)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
