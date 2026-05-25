#!/usr/bin/env python3
"""Validate '。' punctuation rule for answer choices (Phần 5.8 of rule_doc_hieu.md).

Rule:
- Câu hoàn chỉnh (kết thúc bằng である/だ/です/した/ました/べきだ/必要がある/た...) → CẦN '。'
- Mệnh đề phụ (kết thúc bằng から/ため/ので/が/て) → KHÔNG '。'
- Cụm danh từ hoá (kết thúc bằng こと/もの/とき/ている) → KHÔNG '。'
- Danh từ kanji-ending (生き方, 立場, 区別, 壁, 深層...) → KHÔNG '。'
- Nhất quán trong 1 câu hỏi: tất cả 4 options phải cùng style (all có '。' hoặc all không)

Usage:
    python3 check_answer_punctuation.py --csv sheets/samples_v1.csv

Exits with code 1 if any row has incorrect punctuation.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# Endings that REQUIRE 。
COMPLETE_SENTENCE_ENDINGS = [
    "である", "であった",
    "だ", "だった",
    "です", "でした", "ます", "ました",
    "ません", "ません。",
    "した", "した。", "る", "た",
    "べきだ", "べきである",
    "必要がある",
    "らしい", "ようだ", "そうだ",
]

# Endings that FORBID 。 (subordinate clauses)
SUBORDINATE_ENDINGS = [
    "から", "ため", "ので", "ように", "ために",
    "が", "て", "で",
    "こと", "もの", "とき", "ところ",
    "ている", "ていること",
    "ということ", "ためでない",
]

# Kanji range
KANJI_RE = re.compile(r"[一-鿿]")


def classify_ending(option: str) -> tuple[str, str]:
    """Classify an option's ending.

    Returns (class, reason):
      ("complete", "ends with である") → needs 。
      ("subordinate", "ends with から") → no 。
      ("kanji_noun", "ends with kanji") → no 。
      ("unknown", "...") → cannot determine
    """
    # Strip trailing whitespace + 。
    text = option.rstrip()
    has_period = text.endswith("。")
    if has_period:
        text_no_period = text[:-1].rstrip()
    else:
        text_no_period = text

    # Check subordinate endings first (most specific)
    for ending in sorted(SUBORDINATE_ENDINGS, key=len, reverse=True):
        if text_no_period.endswith(ending):
            return ("subordinate", f"ends with '{ending}'", has_period)

    # Check complete sentence endings
    for ending in sorted(COMPLETE_SENTENCE_ENDINGS, key=len, reverse=True):
        if text_no_period.endswith(ending):
            return ("complete", f"ends with '{ending}'", has_period)

    # Check if ends with kanji (and no copula after)
    if text_no_period and KANJI_RE.match(text_no_period[-1]):
        return ("kanji_noun", f"ends with kanji '{text_no_period[-1]}' (noun)", has_period)

    return ("unknown", "cannot classify", has_period)


def check_options(answer_field: str, q_num: int) -> list[str]:
    """Check 4 options in a single answer field. Returns list of errors."""
    if not answer_field or not answer_field.strip():
        return []

    options = answer_field.split("\n")
    if len(options) != 4:
        # already caught by check_csv_fields; skip here
        return []

    errors: list[str] = []

    # Classify each option
    classifications = []
    for i, opt in enumerate(options, 1):
        opt = opt.strip()
        if not opt:
            continue
        cls, reason, has_period = classify_ending(opt)
        classifications.append((i, opt, cls, reason, has_period))

        # Rule violation: subordinate/kanji_noun with 。
        if cls in ("subordinate", "kanji_noun") and has_period:
            errors.append(
                f"Q{q_num} option {i}: `{opt[:30]}...` — {reason} → CẤM '。' (mệnh đề/danh từ, không câu hoàn chỉnh)"
            )
        # Rule violation: complete sentence WITHOUT 。
        if cls == "complete" and not has_period:
            errors.append(
                f"Q{q_num} option {i}: `{opt[:30]}...` — {reason} → CẦN '。' (câu hoàn chỉnh)"
            )

    # Check consistency: all options should have same period style
    if classifications:
        has_period_set = set(c[4] for c in classifications)
        if len(has_period_set) > 1:
            with_period = sum(1 for c in classifications if c[4])
            without_period = len(classifications) - with_period
            errors.append(
                f"Q{q_num} KHÔNG nhất quán: {with_period} option có '。', {without_period} không có '。' "
                f"— tất cả 4 options phải cùng style"
            )

    return errors


def check_row(row: dict, row_idx: int) -> list[str]:
    """Check all answer fields in a row."""
    errors: list[str] = []
    rid = (row.get("_id") or "").strip() or f"row#{row_idx}"

    for i in range(1, 6):
        ans = row.get(f"answer_{i}") or ""
        if not ans.strip():
            continue
        opt_errors = check_options(ans, i)
        errors.extend(opt_errors)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Check '。' punctuation rule for answer choices")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--max-errors-per-row", type=int, default=10)
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    rows_with_errors = 0
    total_rows = 0
    total_errors = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            total_rows += 1
            errors = check_row(row, idx)
            if errors:
                rows_with_errors += 1
                total_errors += len(errors)
                rid = row.get("_id") or f"row#{idx}"
                print(f"FAIL row #{idx} `{rid}` — {len(errors)} error(s):")
                for err in errors[:args.max_errors_per_row]:
                    print(f"  - {err}")
                if len(errors) > args.max_errors_per_row:
                    print(f"  ... and {len(errors) - args.max_errors_per_row} more")
                print()

    print("=" * 60)
    print(f"SUMMARY: {total_rows} rows checked")
    print(f"  Rows with errors: {rows_with_errors}")
    print(f"  Total errors: {total_errors}")
    if rows_with_errors == 0:
        print("  ALL ROWS VALID")
        return 0
    else:
        print(f"  FAIL — {rows_with_errors} row(s) cần fix")
        return 1


if __name__ == "__main__":
    sys.exit(main())
