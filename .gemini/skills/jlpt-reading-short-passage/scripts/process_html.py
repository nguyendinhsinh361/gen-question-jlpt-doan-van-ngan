#!/usr/bin/env python3
"""
process_html.py — Pipeline for JLPT "đoạn văn ngắn" (short-passage) HTML files.

Does three things — NO screenshot PNG (đoạn văn ngắn chỉ xuất HTML + CSV):
  1. Count visible body characters (JLPT standard)
  2. Extract clean HTML (no attributes / no <rt> text / collapsed whitespace)
  3. Append / update rows in the 45-column question_sheet.csv

Usage
-----
# Count chars only (nhanh)
python3 process_html.py --count-only --file assets/html/doan_van_ngan/N3_abcdef.html

# Count chars for all files in a directory
python3 process_html.py --count-only --html-dir assets/html/doan_van_ngan

# Validate Target Range + Hard Reject cho cả batch
python3 process_html.py --validate --html-dir assets/html/doan_van_ngan

# Full pipeline cho 1 bài (có full CSV row)
python3 process_html.py \
    --file assets/html/doan_van_ngan/N3_abcdef.html \
    --csv sheets/samples_v1.csv \
    --tag "daily life" \
    --question-label question_content_match \
    --question "本文の内容と合うものはどれか。" \
    --answers "選択肢1|選択肢2|選択肢3|選択肢4" \
    --correct 2 \
    --explain-vn "..." \
    --explain-en "..."

# Batch mode: rebuild clean HTML + char count cho tất cả file trong thư mục
# (giữ nguyên các column câu hỏi đã có, chỉ refresh text_read + jp_char_count)
python3 process_html.py --html-dir assets/html/doan_van_ngan --csv sheets/samples_v1.csv --refresh

Quy ước filename
----------------
Filename PHẢI đúng format `{LEVEL}_{uuid32hex}.html`. `_id` trong CSV = filename without extension.

Ví dụ: `N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5.html` → `_id` = `N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5`, `level` = `N3`.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# ── Constants ───────────────────────────────────────────────────────

KIND = "đoạn văn ngắn"

# Target ranges (P25–P75 của data mẫu). Dưới ngưỡng Hard Reject → gen lại.
TARGET_RANGE = {
    "N1": (220, 260),
    "N2": (240, 290),
    "N3": (220, 290),
    "N4": (180, 240),
    "N5": (100, 160),
}
HARD_REJECT = {  # bắt buộc gen lại nếu < threshold này
    "N1": 200,
    "N2": 200,
    "N3": 200,
    "N4": 150,
    "N5": 80,
}

CSV_FIELDNAMES = [
    "_id", "level", "tag", "jp_char_count", "kind", "general_audio", "general_image",
    "text_read", "text_read_vn", "text_read_en",
    "question_label_1", "question_1", "question_image_1", "answer_1", "correct_answer_1", "explain_vn_1", "explain_en_1",
    "question_label_2", "question_2", "question_image_2", "answer_2", "correct_answer_2", "explain_vn_2", "explain_en_2",
    "question_label_3", "question_3", "question_image_3", "answer_3", "correct_answer_3", "explain_vn_3", "explain_en_3",
    "question_label_4", "question_4", "question_image_4", "answer_4", "correct_answer_4", "explain_vn_4", "explain_en_4",
    "question_label_5", "question_5", "question_image_5", "answer_5", "correct_answer_5", "explain_vn_5", "explain_en_5",
]

FILENAME_RE = re.compile(r"^(N[1-5])_([0-9a-fA-F]{8,})$")


# ── Character Counting ──────────────────────────────────────────────

class BodyTextExtractor(HTMLParser):
    """Visible body text, skipping <rt>, <style>, <script>."""
    def __init__(self):
        super().__init__()
        self.texts: list[str] = []
        self.skip_depth = 0
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
        if tag in ("rt", "style", "script"):
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in ("rt", "style", "script"):
            self.skip_depth -= 1

    def handle_data(self, d):
        if self.in_body and self.skip_depth == 0:
            self.texts.append(d)


def count_body_chars(html_string: str) -> int:
    """Count visible body chars (JLPT standard) — skip whitespace + full-width space."""
    ext = BodyTextExtractor()
    ext.feed(html_string)
    text = "".join(ext.texts)
    return len(re.sub(r"[ \t\n\r\u3000]", "", text))


# ── Clean HTML Extraction ───────────────────────────────────────────

class CleanHTMLExtractor(HTMLParser):
    """Body HTML with attrs/classes stripped and <rt>/<style>/<script> removed."""
    def __init__(self):
        super().__init__()
        self.result: list[str] = []
        self.skip_depth = 0
        self.in_body = False
        self.body_done = False

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
            return
        if not self.in_body or self.body_done:
            return
        if tag in ("style", "script", "rt"):
            self.skip_depth += 1
            return
        if self.skip_depth > 0:
            return
        self.result.append(f"<{tag}>")

    def handle_startendtag(self, tag, attrs):
        # Void / self-closing tags (ví dụ <br/>)
        if not self.in_body or self.body_done or self.skip_depth > 0:
            return
        if tag in ("style", "script", "rt"):
            return
        self.result.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag == "body":
            self.body_done = True
            return
        if not self.in_body or self.body_done:
            return
        if tag in ("style", "script", "rt"):
            self.skip_depth -= 1
            return
        if self.skip_depth > 0:
            return
        self.result.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.in_body or self.body_done or self.skip_depth > 0:
            return
        self.result.append(data)


def clean_html(full_html: str) -> str:
    ext = CleanHTMLExtractor()
    ext.feed(full_html)
    raw = "".join(ext.result)
    raw = re.sub(r"\s+", " ", raw)
    raw = re.sub(r"\s*<", "<", raw)
    raw = re.sub(r">\s*", ">", raw)
    raw = re.sub(r"<(\w+)></\1>", "", raw)  # bỏ tag rỗng
    return raw.strip()


# ── Filename / ID helpers ───────────────────────────────────────────

def parse_filename(path: str) -> tuple[str | None, str]:
    """`assets/html/doan_van_ngan/N3_abcdef.html` → ('N3', 'N3_abcdef')."""
    stem = Path(path).stem
    m = FILENAME_RE.match(stem)
    if m:
        return m.group(1).upper(), stem
    return None, stem


# ── Validation ──────────────────────────────────────────────────────

def classify_char_count(level: str | None, chars: int) -> str:
    """Return one of: OK / UNDER_TARGET / HARD_REJECT / OVER_TARGET / UNKNOWN_LEVEL."""
    if level not in TARGET_RANGE:
        return "UNKNOWN_LEVEL"
    lo, hi = TARGET_RANGE[level]
    hard = HARD_REJECT[level]
    if chars < hard:
        return "HARD_REJECT"
    if chars < lo:
        return "UNDER_TARGET"
    if chars > hi + 30:  # cho phép hơi dài hơn hi, nhưng quá nhiều thì cảnh báo
        return "OVER_TARGET"
    return "OK"


RUBY_BLOCK = re.compile(r"<ruby[^>]*>(.*?)</ruby>", re.DOTALL)
RT_INNER = re.compile(r"<rt[^>]*>([^<]*)</rt>")


def check_ruby_rt(html: str) -> list[str]:
    """Find <ruby>...</ruby> tags missing <rt> OR with empty/whitespace-only <rt>.
    Returns list of broken snippets (e.g. '<ruby>諦</ruby>' or '<ruby>諦<rt></rt></ruby>').
    Without non-empty <rt>, browser CANNOT render furigana."""
    broken = []
    for m in RUBY_BLOCK.finditer(html):
        full = m.group(0)
        inner = m.group(1)
        rt_contents = RT_INNER.findall(inner)
        if not rt_contents:
            # No <rt> tag at all
            broken.append(full)
        elif not any(rt.strip() for rt in rt_contents):
            # Has <rt> but all empty/whitespace — no furigana to render
            broken.append(full)
    return broken


def validate_file(html_path: str) -> dict:
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    level, name = parse_filename(html_path)
    chars = count_body_chars(html)
    status = classify_char_count(level, chars)
    target = TARGET_RANGE.get(level) if level else None
    broken_ruby = check_ruby_rt(html)
    return {
        "file": html_path,
        "name": name,
        "level": level,
        "chars": chars,
        "target": target,
        "status": status,
        "broken_ruby": broken_ruby,
    }


# ── CSV Operations ──────────────────────────────────────────────────

def empty_row() -> dict:
    return {field: "" for field in CSV_FIELDNAMES}


def build_csv_row(
    html_path: str,
    *,
    tag: str = "",
    question_label: str = "",
    question: str = "",
    answers: str = "",
    correct: str = "",
    explain_vn: str = "",
    explain_en: str = "",
) -> dict:
    with open(html_path, "r", encoding="utf-8") as f:
        full_html = f.read()
    level, name = parse_filename(html_path)
    if level is None:
        raise ValueError(
            f"Filename '{Path(html_path).name}' không đúng format {{LEVEL}}_{{uuid32hex}}.html. "
            f"Ví dụ hợp lệ: N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5.html"
        )
    char_count = count_body_chars(full_html)
    cleaned = clean_html(full_html)

    row = empty_row()
    row.update({
        "_id": name,
        "level": level,
        "tag": tag,
        "jp_char_count": str(char_count),
        "kind": KIND,
        "general_audio": "",
        "general_image": "",  # đoạn văn ngắn KHÔNG có PNG
        "text_read": cleaned,
        "text_read_vn": "",
        "text_read_en": "",
        "question_label_1": question_label,
        "question_1": question,
        "question_image_1": "",
        "answer_1": answers,
        "correct_answer_1": correct,
        "explain_vn_1": explain_vn,
        "explain_en_1": explain_en,
    })
    return row


def load_csv(csv_path: str) -> list[dict]:
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def write_csv(csv_path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDNAMES})


def upsert_row(existing: list[dict], new_row: dict) -> list[dict]:
    """Upsert by _id. Nếu _id đã có, overwrite; ngược lại append."""
    key = new_row.get("_id", "")
    for i, row in enumerate(existing):
        if row.get("_id", "") == key and key:
            existing[i] = new_row
            return existing
    existing.append(new_row)
    return existing


def refresh_row(existing_row: dict, html_path: str) -> dict:
    """Chỉ refresh jp_char_count + text_read + kind từ file HTML, giữ nguyên phần câu hỏi."""
    with open(html_path, "r", encoding="utf-8") as f:
        full_html = f.read()
    chars = count_body_chars(full_html)
    cleaned = clean_html(full_html)
    existing_row["jp_char_count"] = str(chars)
    existing_row["kind"] = KIND
    existing_row["text_read"] = cleaned
    existing_row["general_image"] = ""  # enforce empty
    return existing_row


# ── CLI ─────────────────────────────────────────────────────────────

def cmd_count(files: list[str]) -> int:
    """--count-only: in char count, không ghi CSV. Return 1 nếu có file dưới Hard Reject."""
    print(f"Counting {len(files)} file(s)...\n")
    any_hard_reject = False
    for f in files:
        info = validate_file(f)
        marker = ""
        if info["status"] == "HARD_REJECT":
            marker = "  🚫 HARD REJECT"
            any_hard_reject = True
        elif info["status"] == "UNDER_TARGET":
            marker = "  ⚠️  UNDER TARGET"
        elif info["status"] == "OVER_TARGET":
            marker = "  ⚠️  OVER TARGET"
        elif info["status"] == "UNKNOWN_LEVEL":
            marker = "  ❓ UNKNOWN LEVEL"
        tgt = f"target {info['target'][0]}-{info['target'][1]}" if info["target"] else ""
        print(f"  {info['name']}: {info['chars']} chars [{info['level']}] {tgt}{marker}")
        if info["broken_ruby"]:
            for br in info["broken_ruby"]:
                print(f"    🚫 BROKEN RUBY (thiếu <rt>): {br}")
            any_hard_reject = True
    return 1 if any_hard_reject else 0


def cmd_validate(files: list[str]) -> int:
    """--validate: giống --count-only nhưng exit code 1 nếu bất kỳ file nào UNDER_TARGET hoặc tệ hơn."""
    print(f"Validating {len(files)} file(s)...\n")
    fails = 0
    for f in files:
        info = validate_file(f)
        ruby_ok = len(info["broken_ruby"]) == 0
        ok = info["status"] == "OK" and ruby_ok
        badge = "✅" if ok else ("🚫" if info["status"] == "HARD_REJECT" or not ruby_ok else "⚠️ ")
        tgt = f"target {info['target'][0]}-{info['target'][1]}" if info["target"] else "target ?"
        print(f"  {badge} {info['name']}: {info['chars']} chars [{info['level']}] {tgt} — {info['status']}")
        if info["broken_ruby"]:
            for br in info["broken_ruby"]:
                print(f"       🚫 BROKEN RUBY (thiếu <rt>): {br}")
        if not ok:
            fails += 1
    print(f"\n{len(files) - fails}/{len(files)} files OK.")
    return 1 if fails else 0


def cmd_refresh(files: list[str], csv_path: str) -> None:
    """Refresh jp_char_count + text_read cho các row tồn tại. Thêm row mới với chỉ meta nếu chưa có."""
    rows = load_csv(csv_path)
    by_id = {r.get("_id", ""): r for r in rows}
    updated, added = 0, 0
    for f in files:
        level, name = parse_filename(f)
        if level is None:
            print(f"  [skip] {Path(f).name} — filename không hợp lệ")
            continue
        if name in by_id:
            refresh_row(by_id[name], f)
            updated += 1
        else:
            rows.append(build_csv_row(f))
            added += 1
    write_csv(csv_path, rows)
    print(f"Refreshed {updated} existing row(s), added {added} new row(s) → {csv_path}")


def cmd_single_full(args) -> None:
    """Full pipeline cho 1 bài: build row từ file + CLI args, upsert vào CSV."""
    row = build_csv_row(
        args.file,
        tag=args.tag or "",
        question_label=args.question_label or "",
        question=args.question or "",
        answers="\n".join(opt.strip() for opt in (args.answers or "").split("|")) if args.answers else "",
        correct=str(args.correct) if args.correct else "",
        explain_vn=args.explain_vn or "",
        explain_en=args.explain_en or "",
    )
    # In-file validation
    level = row["level"]
    chars = int(row["jp_char_count"])
    status = classify_char_count(level, chars)
    if status == "HARD_REJECT":
        print(f"🚫 {row['_id']}: {chars} chars — dưới Hard Reject ({HARD_REJECT[level]}). GEN LẠI, không commit CSV.")
        sys.exit(1)
    if status == "UNDER_TARGET":
        print(f"⚠️  {row['_id']}: {chars} chars — dưới Target Range {TARGET_RANGE[level]}. Cân nhắc bổ sung.")
    # Check ruby/rt
    with open(args.file, "r", encoding="utf-8") as fh:
        broken = check_ruby_rt(fh.read())
    if broken:
        for br in broken:
            print(f"🚫 {row['_id']}: BROKEN RUBY (thiếu <rt>): {br}")
        print("    → Sửa HTML thêm <rt> rồi chạy lại. Không commit CSV.")
        sys.exit(1)

    rows = load_csv(args.csv)
    rows = upsert_row(rows, row)
    write_csv(args.csv, rows)
    print(f"✅ Upserted {row['_id']} ({chars} chars, {level}) → {args.csv}")


def collect_files(args) -> list[str]:
    if args.file:
        return [args.file]
    if args.html_dir:
        return sorted(
            os.path.join(args.html_dir, f)
            for f in os.listdir(args.html_dir)
            if f.endswith(".html")
        )
    print("Provide --file or --html-dir", file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(
        description="Process JLPT 'đoạn văn ngắn' HTML files (no screenshot).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--file", help="Single HTML file")
    ap.add_argument("--html-dir", help="Directory with HTML files")
    ap.add_argument("--csv", help="CSV file path (default: sheets/samples_v1.csv)",
                    default="sheets/samples_v1.csv")

    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--count-only", action="store_true",
                      help="In char count, không ghi CSV.")
    mode.add_argument("--validate", action="store_true",
                      help="Kiểm tra tất cả file đạt Target Range. Exit 1 nếu có file fail.")
    mode.add_argument("--refresh", action="store_true",
                      help="Refresh jp_char_count + text_read trong CSV (giữ câu hỏi).")

    # Các arg cho single-file full pipeline (khi không chạy mode nào ở trên)
    ap.add_argument("--tag", help="Topic tag (e.g. 'nhật ký', 'kinh tế')")
    ap.add_argument("--question-label", help="question_label_1 value")
    ap.add_argument("--question", help="Câu hỏi tiếng Nhật")
    ap.add_argument("--answers", help="4 đáp án ngăn cách bởi |, ví dụ 'A|B|C|D'")
    ap.add_argument("--correct", type=int, help="Correct answer index (1-4)")
    ap.add_argument("--explain-vn", help="Giải thích tiếng Việt")
    ap.add_argument("--explain-en", help="Giải thích tiếng Anh")

    args = ap.parse_args()
    files = collect_files(args)

    if args.count_only:
        sys.exit(cmd_count(files))
    if args.validate:
        sys.exit(cmd_validate(files))
    if args.refresh:
        cmd_refresh(files, args.csv)
        return

    # Default: nếu 1 file + có --question thì full pipeline; ngược lại thì in count + cảnh báo.
    if args.file and (args.question or args.question_label):
        cmd_single_full(args)
        return
    if args.html_dir and not args.file:
        print("⚠️  Chạy --html-dir mà không có --refresh/--count-only/--validate.")
        print("    Mặc định chỉ in char count. Dùng --refresh để update CSV.\n")
        sys.exit(cmd_count(files))
    # Single file, không có question args → count only
    sys.exit(cmd_count(files))


if __name__ == "__main__":
    main()
