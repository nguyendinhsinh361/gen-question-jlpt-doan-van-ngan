#!/usr/bin/env python3
"""Validate required CSV fields for JLPT reading output (all dạng).

Checks every row for required fields:
- `_id`: must match `{LEVEL}_<hex>` format (case-insensitive prefix)
- `level`: must be N1/N2/N3/N4/N5 and match _id prefix (case-insensitive)
- `tag`: must be non-empty (recommend English from topic.json)
- `kind`: must match expected kind for this dạng
- `jp_char_count`: must be positive integer
- Q slots: per-level Q count rules:
  * `question_label_{i}`, `question_{i}`, `answer_{i}`, `correct_answer_{i}`,
    `explain_vn_{i}`, `explain_en_{i}` all required for active slots
  * Unused slots must be empty
- Label rules per dạng:
  * integrated: all Q labels = `question_comprehensive_understanding`
  * thematic/long: last Q label = `question_author_opinion` or `question_content_match`

Usage:
    python3 check_csv_fields.py --csv sheets/samples_v1.csv --kind short
    python3 check_csv_fields.py --csv sheets/samples_v1.csv --kind medium
    python3 check_csv_fields.py --csv sheets/samples_v1.csv --kind long
    python3 check_csv_fields.py --csv sheets/samples_v1.csv --kind thematic
    python3 check_csv_fields.py --csv sheets/samples_v1.csv --kind integrated
    python3 check_csv_fields.py --csv sheets/samples_v1.csv --kind info

Exit code 1 if any row has missing/invalid required fields.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# Kind configs — Q count per level + tail-label rules + scope restrictions
KIND_CONFIG = {
    "short": {
        "kind_value": "đoạn văn ngắn",
        "q_count_by_level": {"N1": 1, "N2": 1, "N3": 1, "N4": 1, "N5": 1},
        "allowed_levels": {"N1", "N2", "N3", "N4", "N5"},
        "tail_label_required": None,
        "fixed_label": None,
    },
    "medium": {
        "kind_value": "đoạn văn vừa",
        "q_count_by_level": {"N1": 2, "N2": 2, "N3": 3, "N4": 3, "N5": 2},
        "allowed_levels": {"N1", "N2", "N3", "N4", "N5"},
        "tail_label_required": None,
        "fixed_label": None,
    },
    "long": {
        "kind_value": "đoạn văn dài",
        "q_count_by_level": {"N1": 3, "N3": 4},
        "allowed_levels": {"N1", "N3"},
        "tail_label_required": {"question_author_opinion", "question_content_match"},
        "fixed_label": None,
    },
    "thematic": {
        "kind_value": "đọc hiểu chủ đề",
        "q_count_by_level": {"N1": 3, "N2": 3},
        "allowed_levels": {"N1", "N2"},
        "tail_label_required": {"question_author_opinion", "question_content_match"},
        "fixed_label": None,
    },
    "integrated": {
        "kind_value": "đọc hiểu tổng hợp",
        "q_count_by_level": {"N1": 2, "N2": 2},
        "allowed_levels": {"N1", "N2"},
        "tail_label_required": None,
        "fixed_label": "question_comprehensive_understanding",
    },
    "info": {
        "kind_value": "tìm thông tin",
        "q_count_by_level": {"N1": 2, "N2": 2, "N3": 2, "N4": 2, "N5": 1},
        "allowed_levels": {"N1", "N2", "N3", "N4", "N5"},
        "tail_label_required": None,
        "fixed_label": None,
    },
}

# Case-insensitive prefix `n5` or `N5`, hex of any length ≥ 1
ID_RE = re.compile(r"^([nN][1-5])_([a-fA-F0-9]+)$")
LEVEL_VALUES = {"N1", "N2", "N3", "N4", "N5"}


def check_row(row: dict, cfg: dict, row_idx: int) -> list[str]:
    """Validate a single CSV row. Returns list of error strings (empty if all OK)."""
    errors: list[str] = []
    rid = (row.get("_id") or "").strip()

    if not rid:
        errors.append("MISSING `_id`")
        return errors
    m = ID_RE.match(rid)
    if not m:
        errors.append(f"INVALID `_id` format `{rid}` (expected `N1-N5_<hex>` or `n1-n5_<hex>`)")
        return errors
    id_level = m.group(1).upper()

    level = (row.get("level") or "").strip().upper()
    if not level:
        errors.append("MISSING `level`")
    elif level not in LEVEL_VALUES:
        errors.append(f"INVALID `level`=`{level}` (must be N1/N2/N3/N4/N5)")
    elif level != id_level:
        errors.append(f"MISMATCH `level`=`{level}` vs `_id` prefix `{id_level}`")

    if level in LEVEL_VALUES and level not in cfg["allowed_levels"]:
        errors.append(
            f"LEVEL `{level}` không áp dụng cho kind `{cfg['kind_value']}` "
            f"(chỉ {sorted(cfg['allowed_levels'])})"
        )

    tag = (row.get("tag") or "").strip()
    if not tag:
        errors.append("MISSING `tag` (must be English topic from topic.json)")
    elif re.search(r"[぀-ゟ゠-ヿ一-鿿]", tag):
        errors.append(f"INVALID `tag`=`{tag}` (chứa kana/kanji — phải English)")
    elif re.search(r"[àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠÂẦẤẨẪẬĂẰẮẲẴẶÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]", tag):
        errors.append(f"INVALID `tag`=`{tag}` (chứa diacritic Vietnamese — phải English)")

    kind = (row.get("kind") or "").strip()
    if not kind:
        errors.append(f"MISSING `kind` (expected `{cfg['kind_value']}`)")
    elif kind != cfg["kind_value"]:
        errors.append(f"WRONG `kind`=`{kind}` (expected `{cfg['kind_value']}`)")

    cc_raw = (row.get("jp_char_count") or "").strip()
    if not cc_raw:
        errors.append("MISSING `jp_char_count`")
    else:
        try:
            cc_int = int(cc_raw)
            if cc_int <= 0:
                errors.append(f"INVALID `jp_char_count`={cc_int} (must be > 0)")
        except ValueError:
            errors.append(f"INVALID `jp_char_count`=`{cc_raw}` (not integer)")

    if level in cfg["q_count_by_level"]:
        expected_q = cfg["q_count_by_level"][level]
    else:
        return errors

    required_q_fields = ["question_label_{i}", "question_{i}", "answer_{i}",
                          "correct_answer_{i}", "explain_vn_{i}", "explain_en_{i}"]

    labels_collected: list[str] = []
    for i in range(1, expected_q + 1):
        for field_tmpl in required_q_fields:
            field = field_tmpl.format(i=i)
            val = (row.get(field) or "").strip()
            if not val:
                errors.append(f"MISSING `{field}` (Q slot {i} active for level {level})")

        label = (row.get(f"question_label_{i}") or "").strip()
        labels_collected.append(label)
        if label and not label.startswith("question_"):
            errors.append(f"INVALID `question_label_{i}`=`{label}` (must start with `question_`)")

        ca = (row.get(f"correct_answer_{i}") or "").strip()
        if ca:
            try:
                ca_int = int(ca)
                if ca_int < 1 or ca_int > 4:
                    errors.append(f"INVALID `correct_answer_{i}`={ca_int} (must be 1-4)")
            except ValueError:
                errors.append(f"INVALID `correct_answer_{i}`=`{ca}` (not integer)")

        ans = row.get(f"answer_{i}") or ""
        if ans:
            opts = ans.split("\n")
            if len(opts) != 4:
                errors.append(f"INVALID `answer_{i}`: phải có 4 options (newline-separated), có {len(opts)}")
            for j, opt in enumerate(opts, 1):
                if re.match(r"^\s*([1-4][.\)]|[①②③④])\s", opt):
                    errors.append(f"INVALID `answer_{i}` option {j}: có prefix `1.` `①` — cấm")

    for i in range(expected_q + 1, 6):
        for field_tmpl in required_q_fields:
            field = field_tmpl.format(i=i)
            val = (row.get(field) or "").strip()
            if val:
                errors.append(f"UNUSED slot {i} không empty: `{field}`=`{val[:40]}...`")

    if cfg.get("fixed_label"):
        for idx, lbl in enumerate(labels_collected, 1):
            if lbl and lbl != cfg["fixed_label"]:
                errors.append(
                    f"WRONG `question_label_{idx}`=`{lbl}` — kind `{cfg['kind_value']}` "
                    f"BẮT BUỘC dùng `{cfg['fixed_label']}` cho mọi Q"
                )

    if cfg.get("tail_label_required") and labels_collected:
        tail_label = labels_collected[-1]
        if tail_label and tail_label not in cfg["tail_label_required"]:
            errors.append(
                f"WRONG tail label (Q{len(labels_collected)})=`{tail_label}` — "
                f"kind `{cfg['kind_value']}` câu cuối BẮT BUỘC dùng 1 trong "
                f"{sorted(cfg['tail_label_required'])}"
            )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate required CSV fields for JLPT reading kinds")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--kind", required=True, choices=list(KIND_CONFIG.keys()),
                        help="Dạng: short | medium | long | thematic | integrated | info")
    parser.add_argument("--max-errors-per-row", type=int, default=10,
                        help="Show at most N errors per row (default 10)")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    cfg = KIND_CONFIG[args.kind]
    print(f"Kind: {args.kind} (`{cfg['kind_value']}`)")
    print(f"Allowed levels: {sorted(cfg['allowed_levels'])}")
    print(f"Q count by level: {cfg['q_count_by_level']}")
    if cfg.get("fixed_label"):
        print(f"Fixed label: {cfg['fixed_label']}")
    if cfg.get("tail_label_required"):
        print(f"Tail label must be in: {sorted(cfg['tail_label_required'])}")
    print()

    rows_with_errors = 0
    total_rows = 0
    total_errors = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            total_rows += 1
            errors = check_row(row, cfg, idx)
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
