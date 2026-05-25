#!/usr/bin/env python3
"""Automated spacing checker for わかち書き (wakachi-gaki) rule.

Per Phần 2.5 of rule_doc_hieu.md:
- N5: REQUIRED khoảng trắng giữa các cụm từ. MUST dùng 全角スペース (U+3000), CẤM 半角スペース (U+0020)
- N4/N3/N2/N1: KHÔNG dùng khoảng trắng giữa các cụm từ

This script extracts body text from HTML, counts inter-Japanese spaces
(distinguishing full-width U+3000 from half-width U+0020), and reports:
- N5 passages with TOO FEW inter-JP spaces (missing wakachi-gaki)
- N5 passages with HALF-WIDTH spaces (must be U+3000, not U+0020)
- N1-N4 passages with ANY inter-JP spaces

Exits with code 1 if any spacing issues found.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Japanese character ranges
JP_CHAR = r"[一-鿿ぁ-ゟ゠-ヿ々ー]"

# Full-width space (U+3000) — required for N5
FULL_WIDTH_SPACE = "　"

# Half-width space (U+0020) — forbidden for N5 wakachi-gaki
HALF_WIDTH_SPACE = " "

# Inter-JP space patterns
INTER_JP_FULL = re.compile(f"{JP_CHAR}({FULL_WIDTH_SPACE}+){JP_CHAR}")
INTER_JP_HALF = re.compile(f"{JP_CHAR}( +){JP_CHAR}")  # half-width only
INTER_JP_ANY = re.compile(f"{JP_CHAR}([ {FULL_WIDTH_SPACE}\\t]+){JP_CHAR}")

# Space before punctuation
SPACE_BEFORE_PUNCT = re.compile(r"[ 　\t]+[、。！？]")

# JP char regex
JP_CHAR_RE = re.compile(JP_CHAR)

# Level thresholds
THRESHOLDS = {
    "N5": {"min_ratio": 3.0, "max_ratio": 25.0, "wakachi_required": True, "must_be_full_width": True},
    "N4": {"min_ratio": 0.0, "max_ratio": 0.5, "wakachi_required": False, "must_be_full_width": False},
    "N3": {"min_ratio": 0.0, "max_ratio": 0.5, "wakachi_required": False, "must_be_full_width": False},
    "N2": {"min_ratio": 0.0, "max_ratio": 0.5, "wakachi_required": False, "must_be_full_width": False},
    "N1": {"min_ratio": 0.0, "max_ratio": 0.5, "wakachi_required": False, "must_be_full_width": False},
}


def extract_body(html: str) -> str:
    """Extract main passage body."""
    html = re.sub(r"<head[^>]*>.*?</head>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<rt[^>]*>.*?</rt>", "", html, flags=re.DOTALL)

    m = re.search(r'<div[^>]*class=["\'][^"\']*\bpassage\b[^"\']*["\'][^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        body = m.group(1)
    else:
        m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
        body = m.group(1) if m else html

    body = re.sub(r"<[^>]+>", " ", body)
    return body


def normalize_text(text: str) -> str:
    text = re.sub(r"\r?\n", "\n", text)
    return text


def check_spacing(html: str, level: str) -> dict:
    body = extract_body(html)
    body = normalize_text(body)

    lines = [l.strip() for l in body.split("\n") if l.strip()]
    text = "\n".join(lines)

    jp_chars = len(JP_CHAR_RE.findall(text))
    if jp_chars == 0:
        return {
            "level": level, "jp_chars": 0, "inter_jp_any": 0, "inter_jp_full": 0,
            "inter_jp_half": 0, "ratio_pct": 0.0,
            "wakachi_status": "NO_JP_TEXT", "space_before_punct": 0, "errors": [],
        }

    inter_any = INTER_JP_ANY.findall(text)
    inter_full = INTER_JP_FULL.findall(text)
    inter_half = INTER_JP_HALF.findall(text)
    ratio = (len(inter_any) / jp_chars) * 100

    space_before_punct = len(SPACE_BEFORE_PUNCT.findall(text))

    cfg = THRESHOLDS.get(level)
    if cfg is None:
        return {
            "level": level, "jp_chars": jp_chars, "inter_jp_any": len(inter_any),
            "inter_jp_full": len(inter_full), "inter_jp_half": len(inter_half),
            "ratio_pct": round(ratio, 2), "wakachi_status": f"UNKNOWN_LEVEL_{level}",
            "space_before_punct": space_before_punct, "errors": [f"Unknown level {level}"],
        }

    errors = []
    wakachi_status = "OK"

    if cfg["wakachi_required"]:
        # N5: must have wakachi, must use U+3000
        if ratio < cfg["min_ratio"]:
            wakachi_status = "MISSING_WAKACHI"
            errors.append(
                f"N5 yêu cầu わかち書き nhưng ratio chỉ {ratio:.2f}% (cần ≥ {cfg['min_ratio']}%) — "
                f"thêm khoảng trắng 全角 U+3000 giữa các cụm từ"
            )
        elif ratio > cfg["max_ratio"]:
            wakachi_status = "EXCESS_WAKACHI"
            errors.append(
                f"N5 ratio {ratio:.2f}% vượt ngưỡng tối đa {cfg['max_ratio']}% — "
                f"đang chia quá nhiều khoảng trắng"
            )

        # N5: enforce U+3000, forbid U+0020
        if cfg["must_be_full_width"] and len(inter_half) > 0:
            wakachi_status = "HALFWIDTH_IN_N5"
            errors.append(
                f"N5 BẮT BUỘC dùng 全角スペース (U+3000), nhưng phát hiện {len(inter_half)} "
                f"chỗ dùng 半角スペース (U+0020) — replace tất cả 半角→全角"
            )
    else:
        if ratio > cfg["max_ratio"]:
            wakachi_status = "UNEXPECTED_WAKACHI"
            errors.append(
                f"{level} KHÔNG được dùng わかち書き, nhưng ratio = {ratio:.2f}% "
                f"(ngưỡng tối đa {cfg['max_ratio']}%) — bỏ khoảng trắng giữa các từ tiếng Nhật"
            )

    if space_before_punct > 0:
        errors.append(
            f"{space_before_punct} chỗ có khoảng trắng TRƯỚC dấu câu (、。！？) — sai, phải bỏ"
        )

    return {
        "level": level, "jp_chars": jp_chars,
        "inter_jp_any": len(inter_any),
        "inter_jp_full": len(inter_full),
        "inter_jp_half": len(inter_half),
        "ratio_pct": round(ratio, 2),
        "wakachi_status": wakachi_status,
        "space_before_punct": space_before_punct,
        "errors": errors,
    }


def format_report(file_path: Path, result: dict) -> tuple[str, bool]:
    lines = []
    has_error = bool(result["errors"])

    lines.append(
        f"File: {file_path.name} | Level: {result['level']} | "
        f"JP chars: {result['jp_chars']} | Spaces: full={result['inter_jp_full']} "
        f"half={result['inter_jp_half']} (total={result['inter_jp_any']}) | "
        f"Ratio: {result['ratio_pct']}% | Status: {result['wakachi_status']}"
    )

    if result["errors"]:
        for err in result["errors"]:
            lines.append(f"  ERROR: {err}")
    else:
        lines.append("  PASS — Spacing OK")

    return "\n".join(lines), has_error


def extract_level_from_filename(filename: str) -> str | None:
    m = re.match(r"^([nN][1-5])_", filename)
    return m.group(1).upper() if m else None


def main():
    parser = argparse.ArgumentParser(description="Check wakachi-gaki spacing per level rules")
    parser.add_argument("--file", help="Single HTML file")
    parser.add_argument("--html-dir", help="Directory of HTML files (uses filename for level)")
    parser.add_argument("--level", choices=list(THRESHOLDS.keys()), help="Passage level (required for --file)")
    args = parser.parse_args()

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
                print(f"WARN: skipping {html_file.name} — cannot detect level")
                continue
            files_to_check.append((html_file, level))
    else:
        print("ERROR: must provide --file or --html-dir", file=sys.stderr)
        return 2

    total_errors = 0
    for path, level in files_to_check:
        html = path.read_text(encoding="utf-8")
        result = check_spacing(html, level)
        report, has_error = format_report(path, result)
        print(report)
        if has_error:
            total_errors += 1

    print()
    print("=" * 60)
    print(f"SUMMARY: {len(files_to_check)} files checked")
    print(f"  Files with spacing errors: {total_errors}")
    if total_errors == 0:
        print("  ALL FILES VALID")
        return 0
    else:
        print(f"  FAIL — {total_errors} file(s) cần fix")
        return 1


if __name__ == "__main__":
    sys.exit(main())
