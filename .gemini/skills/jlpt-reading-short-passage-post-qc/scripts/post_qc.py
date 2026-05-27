#!/usr/bin/env python3
"""Post-generation QC script for JLPT reading comprehension CSV output.

Runs ALL auto-checks (Tầng 1) on the output CSV and reports PASS/FAIL per row.
Each module copies this script with its own MODULE_CONFIG at the top.

Usage:
    python3 post_qc.py --csv sheets/samples_v1.csv [--verbose] [--json]
    python3 post_qc.py --csv sheets/samples_v1.csv --kanji-csv rules/kanji_jlpt_sensei.csv
    python3 post_qc.py --csv sheets/samples_v1.csv --html-dir assets/html/doan_van_ngan

Exits 0 if all rows PASS, 1 if any FAIL.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# ============================================================
# MODULE CONFIG — OVERRIDE PER MODULE
# ============================================================
MODULE_CONFIG: dict[str, Any] = {
    "kind": "đoạn văn ngắn",
    "kind_slug": "short",           # for check_csv_fields --kind
    "supported_levels": ["N1", "N2", "N3", "N4", "N5"],
    # Char count: {level: (target_min, target_max, hard_reject_min)}
    "char_ranges": {
        "N1": (160, 280, 130),
        "N2": (170, 300, 140),
        "N3": (150, 260, 120),
        "N4": (100, 200, 80),
        "N5": (60, 110, 50),
    },
    # Expected question count per level
    "question_counts": {
        "N1": 1, "N2": 1, "N3": 1, "N4": 1, "N5": 1,
    },
    # N5 requires full-width space (wakachi-gaki)
    "n5_wakachi": True,
    # Whether this module has screenshot (only tim-thong-tin)
    "has_screenshot": False,
    "short_no_numbered_marker": True,
}

# ============================================================
# CONSTANTS
# ============================================================
KANJI_RE = re.compile(r"[一-鿿㐀-䶿]")
RUBY_RE = re.compile(r"<ruby>(.*?)</ruby>", re.DOTALL)
RT_RE = re.compile(r"<rt>(.*?)</rt>", re.DOTALL)
RT_EMPTY_RE = re.compile(r"<ruby>[^<]*<rt>\s*</rt></ruby>")
RUBY_NO_RT_RE = re.compile(r"<ruby>([^<]*)</ruby>")  # ruby without rt
BR_AFTER_PERIOD_RE = re.compile(r"。\s*<br\s*/?>")
LEVEL_RANK = {"N5": 5, "N4": 4, "N3": 3, "N2": 2, "N1": 1}
FULLWIDTH_SPACE = "　"
HALFWIDTH_SPACE = " "

# Valid question labels
VALID_LABELS = {
    "question_content_match",
    "question_content_mismatch",
    "question_reason_explanation",
    "question_reference",
    "question_meaning_interpretation",
    "question_author_opinion",
    "question_fill_in_the_blank",
    "question_information_search",
    "question_comprehensive_understanding",
}


# ============================================================
# CHECK FUNCTIONS
# ============================================================

def check_required_fields(row: dict, row_idx: int) -> list[str]:
    """C3: Check required CSV fields are present and valid."""
    errors = []
    _id = row.get("_id", "").strip()
    level = row.get("level", "").strip()
    tag = row.get("tag", "").strip()
    kind = row.get("kind", "").strip()
    jp_char = row.get("jp_char_count", "").strip()

    if not _id:
        errors.append("_id is empty")
    if level not in LEVEL_RANK:
        errors.append(f"level '{level}' invalid (expected N1-N5)")
    elif level not in MODULE_CONFIG["supported_levels"]:
        errors.append(f"level '{level}' not supported for this module (expected {MODULE_CONFIG['supported_levels']})")
    if not tag:
        errors.append("tag is empty")
    if kind != MODULE_CONFIG["kind"]:
        errors.append(f"kind '{kind}' != expected '{MODULE_CONFIG['kind']}'")
    if not jp_char or not jp_char.isdigit():
        errors.append(f"jp_char_count '{jp_char}' is not a positive integer")

    # _id format: {LEVEL}_{hex}
    if _id and level:
        expected_prefix = level + "_"
        if not _id.startswith(expected_prefix):
            errors.append(f"_id '{_id}' does not start with '{expected_prefix}'")

    return errors


def check_char_count(row: dict, row_idx: int) -> list[str]:
    """C5: Check char count vs target range per level."""
    errors = []
    level = row.get("level", "").strip()
    jp_char_str = row.get("jp_char_count", "").strip()

    if not jp_char_str or not jp_char_str.isdigit() or level not in MODULE_CONFIG["char_ranges"]:
        return []

    jp_char = int(jp_char_str)
    target_min, target_max, hard_reject = MODULE_CONFIG["char_ranges"][level]

    if jp_char < hard_reject:
        errors.append(f"HARD REJECT: jp_char_count={jp_char} < hard_reject={hard_reject} for {level}")
    elif jp_char < target_min:
        errors.append(f"WARNING: jp_char_count={jp_char} < target_min={target_min} for {level} (under target)")
    elif jp_char > target_max + 50:
        errors.append(f"WARNING: jp_char_count={jp_char} > target_max+50={target_max + 50} for {level} (over target)")

    return errors


def check_ruby_integrity(row: dict, row_idx: int) -> list[str]:
    """C6: Check ruby tag integrity in text_read."""
    errors = []
    text_read = row.get("text_read", "")
    if not text_read:
        return ["text_read is empty"]

    # Check for <ruby> without <rt>
    # Find all ruby blocks
    ruby_blocks = RUBY_RE.findall(text_read)
    for block in ruby_blocks:
        rt_matches = RT_RE.findall(block)
        if not rt_matches:
            errors.append(f"ruby block without <rt>: <ruby>{block[:40]}...</ruby>")
        else:
            for rt_content in rt_matches:
                if not rt_content.strip():
                    errors.append(f"ruby block with empty <rt>: block='{block[:40]}...'")

    # Check for naked <ruby>...</ruby> without any <rt> inside
    naked_matches = RUBY_NO_RT_RE.findall(text_read)
    # Filter out false positives (these are also caught above)
    for naked in naked_matches:
        if "<rt" not in naked:
            errors.append(f"ruby without <rt>: <ruby>{naked[:40]}</ruby>")

    # Check for <rt> with empty content via regex on full text
    empty_rt = RT_EMPTY_RE.findall(text_read)
    if empty_rt:
        errors.append(f"Found {len(empty_rt)} ruby tags with empty <rt>")

    # Check partial furigana (Rule B): ruby content should be full word
    # Simple heuristic: if ruby base is a single kanji within a longer compound
    # This is hard to auto-detect perfectly, so we flag short ruby bases
    for match in RUBY_RE.finditer(text_read):
        full_block = match.group(0)
        base_and_rt = match.group(1)
        rt_match = RT_RE.search(base_and_rt)
        if rt_match:
            base = RT_RE.sub("", base_and_rt).strip()
            rt = rt_match.group(1).strip()
            # Check: single kanji base with multi-char reading suggests partial furigana
            if len(base) == 1 and KANJI_RE.match(base) and len(rt) >= 3:
                # Look at surrounding context to see if it's part of a compound
                pos = match.start()
                before = text_read[max(0, pos - 2):pos]
                after_end = match.end()
                after = text_read[after_end:after_end + 2]
                if KANJI_RE.search(before) or KANJI_RE.search(after):
                    errors.append(
                        f"POSSIBLE partial furigana (Rule B): <ruby>{base}<rt>{rt}</rt></ruby>"
                        f" — context: ...{before}[HERE]{after}..."
                    )

    return errors


def check_question_count(row: dict, row_idx: int) -> list[str]:
    """C8: Check expected question count per kind/level."""
    errors = []
    level = row.get("level", "").strip()

    if level not in MODULE_CONFIG["question_counts"]:
        return []

    expected = MODULE_CONFIG["question_counts"][level]

    # Count active questions
    active_q = 0
    for i in range(1, 6):
        q = row.get(f"question_{i}", "").strip()
        if q:
            active_q += 1

    if active_q != expected:
        errors.append(f"question count={active_q}, expected={expected} for {level} {MODULE_CONFIG['kind']}")

    # Check that active question slots have all required fields
    for i in range(1, active_q + 1):
        for field in ["question_label", "question", "answer", "correct_answer", "explain_vn", "explain_en"]:
            col = f"{field}_{i}"
            val = row.get(col, "").strip()
            if not val:
                errors.append(f"active question slot {i} missing {col}")

    # Check that unused slots are empty
    for i in range(active_q + 1, 6):
        for field in ["question_label", "question", "answer", "correct_answer", "explain_vn", "explain_en"]:
            col = f"{field}_{i}"
            val = row.get(col, "").strip()
            if val:
                errors.append(f"unused question slot {i} has value in {col}")

    return errors


def check_question_labels(row: dict, row_idx: int) -> list[str]:
    """Check question labels are valid."""
    errors = []
    for i in range(1, 6):
        label = row.get(f"question_label_{i}", "").strip()
        if label and label not in VALID_LABELS:
            errors.append(f"invalid question_label_{i}: '{label}'")
    return errors


def check_correct_answer(row: dict, row_idx: int) -> list[str]:
    """Check correct_answer is 1-4 and answer has 4 options."""
    errors = []
    level = row.get("level", "").strip()
    if level not in MODULE_CONFIG["question_counts"]:
        return []

    expected_q = MODULE_CONFIG["question_counts"][level]

    for i in range(1, expected_q + 1):
        correct = row.get(f"correct_answer_{i}", "").strip()
        answer = row.get(f"answer_{i}", "").strip()

        if correct and correct not in ("1", "2", "3", "4"):
            errors.append(f"correct_answer_{i}='{correct}' not in 1-4")

        if answer:
            options = answer.split("\n")
            if len(options) != 4:
                errors.append(f"answer_{i} has {len(options)} options (expected 4)")

            # Check option numbering (should NOT have 1. 2. 3. 4. prefix)
            for j, opt in enumerate(options):
                if re.match(r"^\s*[1-4]\.\s", opt):
                    errors.append(f"answer_{i} option {j + 1} has numbered prefix (forbidden)")

    return errors


def check_option_length_ratio(row: dict, row_idx: int) -> list[str]:
    """C10: Check option length ratio < 2.0."""
    errors = []
    level = row.get("level", "").strip()
    if level not in MODULE_CONFIG["question_counts"]:
        return []

    expected_q = MODULE_CONFIG["question_counts"][level]

    for i in range(1, expected_q + 1):
        answer = row.get(f"answer_{i}", "").strip()
        if not answer:
            continue
        options = answer.split("\n")
        if len(options) != 4:
            continue
        lengths = [len(opt.strip()) for opt in options if opt.strip()]
        if not lengths:
            continue
        min_len = min(lengths)
        max_len = max(lengths)
        if min_len > 0:
            ratio = max_len / min_len
            if ratio > 2.0:
                errors.append(
                    f"answer_{i} option length ratio={ratio:.1f} > 2.0 "
                    f"(min={min_len}, max={max_len})"
                )

    return errors


def check_html_antipattern(row: dict, row_idx: int) -> list[str]:
    """C9: Check for 。<br> anti-pattern in text_read."""
    errors = []
    text_read = row.get("text_read", "")

    # N5 letter format is exception
    level = row.get("level", "").strip()
    if level == "N5":
        return []  # N5 allows <br> in letter format

    if BR_AFTER_PERIOD_RE.search(text_read):
        errors.append("text_read contains '。<br>' anti-pattern (use <p> instead)")

    return errors


def check_spacing(row: dict, row_idx: int) -> list[str]:
    """C2: Check wakachi-gaki spacing rules."""
    errors = []
    level = row.get("level", "").strip()

    # Fields to check
    fields_to_check = ["text_read", "question_1", "answer_1"]
    if level not in MODULE_CONFIG["question_counts"]:
        return []
    for i in range(2, MODULE_CONFIG["question_counts"].get(level, 0) + 1):
        fields_to_check.extend([f"question_{i}", f"answer_{i}"])

    for field in fields_to_check:
        val = row.get(field, "")
        if not val:
            continue

        # Strip HTML tags for spacing check
        text = re.sub(r"<[^>]+>", "", val)

        if level == "N5":
            # N5: MUST have full-width spaces (U+3000)
            if FULLWIDTH_SPACE not in text and len(text) > 20:
                errors.append(f"{field}: N5 missing full-width spaces (わかち書き required)")
            # N5: MUST NOT have half-width spaces between Japanese
            jp_context = re.findall(r"[぀-鿿] [぀-鿿]", text)
            if jp_context:
                errors.append(f"{field}: N5 has half-width space (U+0020) between Japanese chars — must use U+3000")
        else:
            # N1-N4: MUST NOT have full-width spaces
            if FULLWIDTH_SPACE in text:
                errors.append(f"{field}: {level} should NOT have full-width spaces (わかち書き is N5 only)")

    return errors


def check_buntai_consistency(row: dict, row_idx: int) -> list[str]:
    """L1 (semi-auto): Check 文体の統一 — desu/masu vs da/dearu consistency.

    N1/N2/N3: should use 普通形 (da/dearu) — flag if です/ます found in Q/A
    N4/N5: should use ます形 — flag if だ。/である。found in Q/A
    """
    errors = []
    level = row.get("level", "").strip()
    if level not in LEVEL_RANK:
        return []

    expected_q = MODULE_CONFIG["question_counts"].get(level, 0)

    for i in range(1, expected_q + 1):
        question = row.get(f"question_{i}", "").strip()
        answer = row.get(f"answer_{i}", "").strip()
        combined = question + "\n" + answer

        if level in ("N1", "N2", "N3"):
            # Should be 普通形 — flag です/ます
            desu_masu_patterns = re.findall(r"(?:です[。か]|ます[。か]|ました[。か]|ません[。か]|でした[。か])", combined)
            if desu_masu_patterns:
                errors.append(
                    f"question/answer_{i}: {level} should use 普通形 but found です/ます patterns: "
                    f"{desu_masu_patterns[:3]}"
                )
        elif level in ("N4", "N5"):
            # Should be ます形 — flag だ。/である。
            da_dearu_patterns = re.findall(r"(?:である[。か]|ではない[。か]|だ[。か](?!ら))", combined)
            if da_dearu_patterns:
                errors.append(
                    f"question/answer_{i}: {level} should use ます形 but found 普通形 patterns: "
                    f"{da_dearu_patterns[:3]}"
                )

    return errors


def check_tag_in_topic_json(row: dict, row_idx: int, topic_tags: set[str] | None) -> list[str]:
    """Check tag is from topic.json catalog."""
    errors = []
    if topic_tags is None:
        return []
    tag = row.get("tag", "").strip()
    if tag and tag not in topic_tags:
        errors.append(f"tag '{tag}' not found in topic.json catalog")
    return errors


# ============================================================
# CROSS-BATCH CHECKS
# ============================================================

def check_correct_answer_distribution(rows: list[dict]) -> list[str]:
    """C7: Check correct answer position distribution across batch."""
    errors = []
    by_level: dict[str, list[int]] = {}

    for row in rows:
        level = row.get("level", "").strip()
        expected_q = MODULE_CONFIG["question_counts"].get(level, 0)
        for i in range(1, expected_q + 1):
            correct = row.get(f"correct_answer_{i}", "").strip()
            if correct in ("1", "2", "3", "4"):
                by_level.setdefault(level, []).append(int(correct))

    for level, positions in by_level.items():
        if len(positions) < 4:
            continue

        counter = Counter(positions)
        total = len(positions)
        for pos in range(1, 5):
            pct = counter.get(pos, 0) / total * 100
            if pct > 50:
                errors.append(
                    f"[{level}] correct_answer position {pos} appears {pct:.0f}% "
                    f"({counter.get(pos, 0)}/{total}) — should be ~25%"
                )

        # Check for 3+ consecutive same position
        for i in range(len(positions) - 2):
            if positions[i] == positions[i + 1] == positions[i + 2]:
                errors.append(
                    f"[{level}] 3+ consecutive correct_answer at position {positions[i]} "
                    f"(rows {i + 1}-{i + 3})"
                )
                break

    return errors


def check_topic_diversity(rows: list[dict]) -> list[str]:
    """B1: Check topic diversity in batch."""
    errors = []
    by_level: dict[str, list[str]] = {}

    for row in rows:
        level = row.get("level", "").strip()
        tag = row.get("tag", "").strip()
        if tag:
            by_level.setdefault(level, []).append(tag)

    for level, tags in by_level.items():
        if len(tags) > 3:
            unique = set(tags)
            if len(unique) < 2:
                errors.append(f"[{level}] all {len(tags)} rows use same tag '{tags[0]}' — need diversity")
        # Check exact duplicates
        counter = Counter(tags)
        for tag, count in counter.items():
            if count > 1:
                errors.append(f"[{level}] tag '{tag}' used {count} times — should be unique per level")

    return errors


def check_label_diversity(rows: list[dict]) -> list[str]:
    """B2: Check question label diversity in batch."""
    errors = []
    by_level: dict[str, list[str]] = {}

    for row in rows:
        level = row.get("level", "").strip()
        expected_q = MODULE_CONFIG["question_counts"].get(level, 0)
        for i in range(1, expected_q + 1):
            label = row.get(f"question_label_{i}", "").strip()
            if label:
                by_level.setdefault(level, []).append(label)

    for level, labels in by_level.items():
        if len(labels) > 3:
            unique = set(labels)
            if len(unique) < 2:
                errors.append(
                    f"[{level}] all {len(labels)} questions use same label '{labels[0]}' "
                    f"— need ≥2 different labels"
                )
        if len(labels) > 5 and len(set(labels)) < 3:
            errors.append(
                f"[{level}] {len(labels)} questions use only {len(set(labels))} labels "
                f"— need ≥3 for batch >5"
            )

    return errors


# ============================================================
# MAIN RUNNER
# ============================================================

def load_topic_tags(rules_dir: Path | None) -> set[str] | None:
    """Load topic tags from topic.json if available."""
    if rules_dir is None:
        return None
    topic_file = rules_dir / "topic.json"
    if not topic_file.exists():
        return None
    try:
        data = json.loads(topic_file.read_text(encoding="utf-8"))
        tags = set()
        for cat in data.get("categories", []):
            for topic in cat.get("topics", []):
                tags.add(topic.get("en", ""))
        return tags
    except Exception:
        return None



# ───────────────────────────────────────────────────────────────────
# New checks per dạng (added per teacher ver2 criteria)
# ───────────────────────────────────────────────────────────────────

def check_short_no_numbered_marker(row: dict, row_idx: int) -> list[str]:
    """C13 (短文 only): 短文 chỉ có 1Q → KHÔNG được dùng ①②③ marker.
    Fill_in dùng [　　] (no number), KHÔNG dùng [ ① ]."""
    if not MODULE_CONFIG.get("short_no_numbered_marker"):
        return []
    errors: list[str] = []
    text_read = row.get("text_read", "") or ""
    # Check for ①②③ etc in text_read
    if re.search(r"[①②③④⑤]", text_read):
        errors.append(f"短文: text_read chứa ①②③ marker (CẤM với 短文 1Q) — dùng gạch chân không số")
    # Check for [ ① ] in text_read (fill_in must use [　　] without number)
    if re.search(r"\[\s*[①②③④⑤]\s*\]", text_read):
        errors.append(f"短文 fill_in: text_read chứa [ ① ] (CẤM với 短文) — dùng [　　] không số")
    return errors


def check_medium_n3_marker_required(row: dict, row_idx: int) -> list[str]:
    """C14 (中文 only): N3 中文 100% bài thực tế có ①②③ + gạch chân.
    Nếu N3 中文 mà text_read không có marker → cảnh báo."""
    if not MODULE_CONFIG.get("n3_requires_markers"):
        return []
    level = row.get("level", "").strip()
    if level != "N3":
        return []
    text_read = row.get("text_read", "") or ""
    has_marker = bool(re.search(r"[①②③]", text_read))
    has_underline = "<u>" in text_read
    if not has_marker and not has_underline:
        return [f"N3 中文: KHÔNG có ①②③ marker NOR <u> — teacher: 100% bài N3 中文 thực tế có ①②③ + gạch chân"]
    return []


def check_integrated_ab_label(row: dict, row_idx: int) -> list[str]:
    """C15 (統合 only): text_read PHẢI có nhãn A và B rõ ràng đầu mỗi đoạn.
    KHÔNG dùng 1/2 hay ①②.
    Cho phép cả 「文章A」「文章B」 hoặc <section class="passage-a"> hoặc 「Ａ」「Ｂ」."""
    if not MODULE_CONFIG.get("require_ab_label"):
        return []
    errors: list[str] = []
    text_read = row.get("text_read", "") or ""
    # Patterns that indicate proper A/B labeling
    has_a = bool(re.search(r"(文章A|class=\"passage-a\"|【A】|＜A＞|Ａ.{0,3}<|^A\s+|>A<|Ｐａｓｓａｇｅ.{0,5}A|相談者|回答者Ａ)", text_read, re.MULTILINE))
    has_b = bool(re.search(r"(文章B|class=\"passage-b\"|【B】|＜B＞|Ｂ.{0,3}<|^B\s+|>B<|Ｐａｓｓａｇｅ.{0,5}B|回答者Ｂ)", text_read, re.MULTILINE))
    if not (has_a and has_b):
        errors.append(f"統合: text_read THIẾU nhãn A/B rõ ràng — phải có 「文章A」「文章B」 hoặc <section class=\"passage-a/b\"> hoặc 相談者+回答者Ａ/Ｂ")
    # Check for forbidden 1/2 or ①② labeling instead of A/B
    if re.search(r"(文章[①②]|文章1[^A-Za-z]|文章2[^A-Za-z])", text_read):
        errors.append(f"統合: text_read dùng 文章1/2 hoặc ①②③ thay vì A/B — phải đổi sang A/B")
    return errors


def check_integrated_fixed_label(row: dict, row_idx: int) -> list[str]:
    """C16 (統合 only): Tất cả question_label_* PHẢI = question_comprehensive_understanding."""
    fixed = MODULE_CONFIG.get("fixed_label")
    if not fixed:
        return []
    errors: list[str] = []
    for i in range(1, 6):
        label = (row.get(f"question_label_{i}") or "").strip()
        if label and label != fixed:
            errors.append(f"統合 Q{i}: question_label_{i}=\"{label}\" — PHẢI là \"{fixed}\"")
    return errors


def check_thematic_tail_label(row: dict, row_idx: int) -> list[str]:
    """C17 (主張 only): Q cuối PHẢI là question_author_opinion hoặc question_content_match."""
    allowed = MODULE_CONFIG.get("tail_label_required")
    if not allowed:
        return []
    level = row.get("level", "").strip()
    q_count = MODULE_CONFIG.get("question_counts", {}).get(level)
    if not q_count:
        return []
    tail_label = (row.get(f"question_label_{q_count}") or "").strip()
    if tail_label and tail_label not in allowed:
        return [f"主張: Q{q_count} (câu cuối) = \"{tail_label}\" — PHẢI là 1 trong {allowed}"]
    return []


def check_quotes_underline_consistency(row: dict, row_idx: int) -> list[str]:
    """C18: Nếu text_read dùng <u>...</u> để đánh dấu cụm,
    question stem PHẢI dùng <u>...</u> KHÔNG bao quanh 「」 (và ngược lại).
    Phần 2.1 teacher ver2: nhất quán 「」 vs <u> giữa text_read và câu hỏi."""
    errors: list[str] = []
    text_read = row.get("text_read", "") or ""
    # Find <u>...</u> spans in text_read
    text_u_spans = re.findall(r"<u>([^<]+)</u>", text_read)
    if not text_u_spans:
        return errors
    # For each question, check that referenced text uses <u>...</u> not 「...」
    for i in range(1, 6):
        q = row.get(f"question_{i}", "") or ""
        if not q.strip():
            continue
        for span in text_u_spans:
            if span and span in q:
                # Check if span is wrapped in 「」 in question
                wrap_pattern = f"「{re.escape(span)}」"
                if re.search(wrap_pattern, q):
                    errors.append(
                        f"Q{i}: cụm \"{span}\" trong text_read dùng <u> nhưng question dùng 「」 — "
                        f"phải nhất quán (Phần 2.1)"
                    )
    return errors


def check_integrated_ab_balance(row: dict, row_idx: int) -> list[str]:
    """C19 (統合 only): A và B độ dài cân bằng — chênh lệch ≤ 30%, mỗi đoạn 40-60% tổng."""
    if MODULE_CONFIG.get("kind_slug") != "integrated":
        return []
    errors: list[str] = []
    text_read = row.get("text_read", "") or ""
    # Split by A/B section markers
    # Try multiple patterns
    a_match = re.search(r'(?:class="passage-a"|【A】|文章A|＜A＞|相談者|回答者[ＡA])(.*?)(?=class="passage-b"|【B】|文章B|＜B＞|回答者[ＢB]|$)', text_read, re.DOTALL)
    b_match = re.search(r'(?:class="passage-b"|【B】|文章B|＜B＞|回答者[ＢB])(.*?)$', text_read, re.DOTALL)
    if not a_match or not b_match:
        return []  # cannot parse — silent (handled by check_integrated_ab_label)
    a_chars = len(re.findall(r"[一-鿿ぁ-ゟ゠-ヿ々ー]", a_match.group(1)))
    b_chars = len(re.findall(r"[一-鿿ぁ-ゟ゠-ヿ々ー]", b_match.group(1)))
    if a_chars == 0 or b_chars == 0:
        return []
    total = a_chars + b_chars
    a_pct = a_chars / total * 100
    b_pct = b_chars / total * 100
    if a_pct < 40 or a_pct > 60:
        errors.append(f"統合 A/B balance vỡ: A={a_pct:.1f}% (yêu cầu 40-60%, chars A={a_chars} B={b_chars})")
    bigger = max(a_chars, b_chars)
    smaller = min(a_chars, b_chars)
    delta = (bigger - smaller) / bigger * 100
    if delta > 30:
        errors.append(f"統合 chênh lệch A-B={delta:.1f}% > 30% (chars A={a_chars} B={b_chars})")
    return errors


def check_info_symbols(row: dict, row_idx: int) -> list[str]:
    """C20 (情報 only): text_read PHẢI có ít nhất 1 ký hiệu đặc trưng — ○ × △ ※ ★ ◆ 【】."""
    if MODULE_CONFIG.get("kind_slug") != "info":
        return []
    text_read = row.get("text_read", "") or ""
    SYMBOLS = "○×△※★◆【】◯■□▲▽"
    if not any(c in text_read for c in SYMBOLS):
        return [f"情報検索: text_read THIẾU ký hiệu đặc trưng ({SYMBOLS}) — bài tìm thông tin phải có table/bullet + ký hiệu"]
    return []


def check_chu_first_occurrence_advisory(row: dict, row_idx: int) -> list[str]:
    """C21: Advisory — flag khi cùng kanji có furigana cả ở text_read và phần question (có thể vi phạm Rule C).

    Rule C: chỉ rắc lần đầu xuất hiện, kể cả 注. Nếu kanji có ruby ở 1 chỗ, các chỗ sau không cần ruby."""
    errors: list[str] = []
    text_read = row.get("text_read", "") or ""
    # Find all <ruby>X<rt>Y</rt></ruby> in text_read
    text_rubies = set(re.findall(r"<ruby>([^<]+)<rt>", text_read))
    if not text_rubies:
        return errors
    # Check questions/answers — if same kanji-word has ruby there, advisory
    for i in range(1, 6):
        for field in [f"question_{i}", f"answer_{i}", f"explain_vn_{i}", f"explain_en_{i}"]:
            content = row.get(field, "") or ""
            if not content:
                continue
            for r in re.findall(r"<ruby>([^<]+)<rt>", content):
                if r in text_rubies:
                    errors.append(
                        f"Rule C advisory: kanji '{r}' có ruby ở cả text_read và {field} — "
                        f"chỉ cần rắc lần đầu xuất hiện"
                    )
                    break  # one error per field
    return errors


def check_chuuryaku_rate(rows: list[dict]) -> list[str]:
    """B5 cross-batch: Rate (中略) per dạng-level so với teacher distribution.

    Teacher:
    - long N1: (中略) ~30-35%
    - thematic N1: (中略) ~40-45%
    - thematic N2: (中略) ~28-35%
    Other dạng: không có (中略).
    """
    if MODULE_CONFIG.get("kind_slug") not in ("long", "thematic"):
        return []
    issues: list[str] = []
    targets = {
        "long":     {"N1": (30, 35), "N3": (0, 5)},
        "thematic": {"N1": (40, 45), "N2": (28, 35)},
    }
    slug = MODULE_CONFIG["kind_slug"]
    if slug not in targets:
        return []
    from collections import defaultdict
    by_level = defaultdict(list)
    for r in rows:
        by_level[r.get("level", "").strip()].append(r)
    for level, expected in targets[slug].items():
        items = by_level.get(level, [])
        if len(items) < 3:
            continue  # need ≥3 to evaluate distribution
        with_chuuryaku = sum(1 for r in items if "(中略)" in (r.get("text_read", "") or "") or "（中略）" in (r.get("text_read", "") or ""))
        actual_pct = with_chuuryaku / len(items) * 100
        lo, hi = expected
        if actual_pct < lo * 0.5 or actual_pct > hi * 1.5:
            issues.append(
                f"(中略) rate cho {level} {slug}: {actual_pct:.0f}% ({with_chuuryaku}/{len(items)}) "
                f"— teacher kỳ vọng {lo}-{hi}% (lệch nhiều)"
            )
    return issues

def run_all_checks(csv_path: Path, rules_dir: Path | None = None, verbose: bool = False) -> dict:
    """Run all checks and return structured report."""
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return {"total": 0, "passed": 0, "failed": 0, "errors": [], "row_results": []}

    topic_tags = load_topic_tags(rules_dir)

    # Per-row checks
    per_row_checks = [
        ("C3_required_fields", check_required_fields),
        ("C5_char_count", check_char_count),
        ("C6_ruby_integrity", check_ruby_integrity),
        ("C8_question_count", check_question_count),
        ("C8b_question_labels", check_question_labels),
        ("C8c_correct_answer", check_correct_answer),
        ("C10_option_length", check_option_length_ratio),
        ("C9_html_antipattern", check_html_antipattern),
        ("C2_spacing", check_spacing),
        ("L1_buntai", check_buntai_consistency),
    ]

    row_results = []
    total_errors = 0

    for i, row in enumerate(rows):
        _id = row.get("_id", f"row_{i}")
        level = row.get("level", "?")
        row_errors: dict[str, list[str]] = {}

        for check_name, check_fn in per_row_checks:
            errs = check_fn(row, i)
            if errs:
                row_errors[check_name] = errs

        # Topic check
        tag_errs = check_tag_in_topic_json(row, i, topic_tags)
        if tag_errs:
            row_errors["B1_topic_valid"] = tag_errs

        passed = len(row_errors) == 0
        error_count = sum(len(v) for v in row_errors.values())
        total_errors += error_count

        row_results.append({
            "row": i + 1,
            "_id": _id,
            "level": level,
            "passed": passed,
            "error_count": error_count,
            "errors": row_errors,
        })

    # Cross-batch checks
    cross_errors = []
    cross_errors.extend(check_correct_answer_distribution(rows))
    cross_errors.extend(check_topic_diversity(rows))
    cross_errors.extend(check_label_diversity(rows))

    passed_count = sum(1 for r in row_results if r["passed"])
    failed_count = len(row_results) - passed_count

    return {
        "csv_path": str(csv_path),
        "module": MODULE_CONFIG["kind"],
        "total": len(rows),
        "passed": passed_count,
        "failed": failed_count,
        "total_errors": total_errors + len(cross_errors),
        "row_results": row_results,
        "cross_batch_errors": cross_errors,
    }


def print_report(report: dict, verbose: bool = False):
    """Print human-readable report."""
    print("=" * 70)
    print(f"POST-QC REPORT — {report['module']}")
    print(f"CSV: {report['csv_path']}")
    print(f"Total rows: {report['total']} | PASS: {report['passed']} | FAIL: {report['failed']}")
    print(f"Total errors: {report['total_errors']}")
    print("=" * 70)

    # Failed rows
    for r in report["row_results"]:
        if not r["passed"]:
            print(f"\n❌ Row {r['row']} [{r['level']}] {r['_id']} — {r['error_count']} error(s):")
            for check, errs in r["errors"].items():
                for err in errs:
                    print(f"   [{check}] {err}")

    if verbose:
        # Passed rows
        for r in report["row_results"]:
            if r["passed"]:
                print(f"\n✅ Row {r['row']} [{r['level']}] {r['_id']} — ALL PASS")

    # Cross-batch
    if report["cross_batch_errors"]:
        print(f"\n{'=' * 70}")
        print("CROSS-BATCH ISSUES:")
        for err in report["cross_batch_errors"]:
            print(f"   ⚠️  {err}")

    # Summary
    print(f"\n{'=' * 70}")
    if report["failed"] == 0 and not report["cross_batch_errors"]:
        print("✅ ALL CHECKS PASSED")
    else:
        print(f"❌ {report['failed']} row(s) failed, {len(report['cross_batch_errors'])} cross-batch issue(s)")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Post-QC for JLPT reading CSV")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--rules-dir", help="Path to rules/ directory (for topic.json)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show passed rows too")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    rules_dir = Path(args.rules_dir) if args.rules_dir else None

    report = run_all_checks(csv_path, rules_dir, args.verbose)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report, args.verbose)

    sys.exit(0 if report["failed"] == 0 and not report["cross_batch_errors"] else 1)


if __name__ == "__main__":
    main()
