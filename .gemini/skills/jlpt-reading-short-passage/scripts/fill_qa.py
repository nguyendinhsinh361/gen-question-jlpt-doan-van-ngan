#!/usr/bin/env python3
"""
Fill Q&A data vào CSV một cách an toàn — tự động handle comma, newline, quoting.
Agent BẮT BUỘC dùng script này, không edit CSV bằng tay.

Đoạn văn ngắn chỉ có 1 câu hỏi (Q1). Các slot Q2-Q5 luôn để rỗng.

Usage:
    python3 fill_qa.py \\
        --csv sheets/N3.csv \\
        --row-id N3_abc123 \\
        --question-label question_content_match \\
        --q1 "この文章の内容と合っているものはどれか。" \\
        --a1 "選択肢1
選択肢2
選択肢3
選択肢4" \\
        --ca1 2 \\
        --evn1 "Đáp án đúng: ...
Đáp án sai: ...
Tóm tắt: ..." \\
        --een1 "Correct answer: ...
Wrong answers: ...
Summary: ..."

question-label hợp lệ (7 loại, theo rules/mission.json):
    question_content_match, question_reason_explanation, question_reference,
    question_meaning_interpretation, question_content_mismatch, question_author_opinion,
    question_fill_in_the_blank
"""
import argparse
import csv
import os
import sys

CSV_FIELDNAMES = [
    "_id", "level", "tag", "jp_char_count", "kind", "general_audio", "general_image",
    "text_read", "text_read_vn", "text_read_en",
    "question_label_1", "question_1", "question_image_1", "answer_1", "correct_answer_1", "explain_vn_1", "explain_en_1",
    "question_label_2", "question_2", "question_image_2", "answer_2", "correct_answer_2", "explain_vn_2", "explain_en_2",
    "question_label_3", "question_3", "question_image_3", "answer_3", "correct_answer_3", "explain_vn_3", "explain_en_3",
    "question_label_4", "question_4", "question_image_4", "answer_4", "correct_answer_4", "explain_vn_4", "explain_en_4",
    "question_label_5", "question_5", "question_image_5", "answer_5", "correct_answer_5", "explain_vn_5", "explain_en_5",
]

VALID_LABELS = {
    "question_content_match",
    "question_reason_explanation",
    "question_reference",
    "question_meaning_interpretation",
    "question_content_mismatch",
    "question_author_opinion",
    "question_fill_in_the_blank",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fill Q&A data vào CSV đoạn văn ngắn (1 question only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--csv", required=True, help="Đường dẫn file CSV (vd sheets/N3.csv)")
    parser.add_argument("--row-id", required=True, help="_id của row cần update")
    parser.add_argument(
        "--question-label",
        required=True,
        help=f"1 trong {sorted(VALID_LABELS)}",
    )
    parser.add_argument("--q1", required=True, help="Câu hỏi (tiếng Nhật)")
    parser.add_argument(
        "--a1",
        required=True,
        help="4 đáp án (newline-separated, KHÔNG prefix '1.', '2.', ...)",
    )
    parser.add_argument("--ca1", required=True, help="correct_answer_1 (1-4)")
    parser.add_argument("--evn1", required=True, help="Explanation VN (3-part format)")
    parser.add_argument("--een1", required=True, help="Explanation EN (3-part format)")
    args = parser.parse_args()

    # Validate question-label
    if args.question_label not in VALID_LABELS:
        print(
            f"❌ --question-label='{args.question_label}' không hợp lệ.\n"
            f"   Các label hợp lệ: {sorted(VALID_LABELS)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate CSV exists
    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"❌ CSV không tồn tại: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # Read CSV
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Find row
    target = None
    for row in rows:
        if row.get("_id") == args.row_id:
            target = row
            break
    if target is None:
        print(
            f"❌ Row _id={args.row_id} không tìm thấy trong {csv_path}\n"
            f"   Hãy chạy process_html.py để tạo row trước.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate answer options (exactly 4, no prefix)
    opts = [x.strip() for x in args.a1.strip().split("\n") if x.strip()]
    if len(opts) != 4:
        print(
            f"❌ answer_1 phải có đúng 4 lựa chọn (thấy {len(opts)}).\n"
            f"   Options: {opts}",
            file=sys.stderr,
        )
        sys.exit(1)
    for i, opt in enumerate(opts, 1):
        # Chặn prefix kiểu "1. ", "1)", "①", "1、"
        if (
            opt[:2].strip() in ("1.", "2.", "3.", "4.", "1)", "2)", "3)", "4)")
            or opt[:1] in ("①", "②", "③", "④")
            or (len(opt) >= 2 and opt[0] in "1234" and opt[1] in "．、)")
        ):
            print(
                f"❌ answer_1 option {i} chứa prefix ('{opt[:2]}'). "
                f"Bỏ prefix đi, chỉ ghi nội dung thuần.",
                file=sys.stderr,
            )
            sys.exit(1)
    a_clean = "\n".join(opts)

    # Validate correct_answer
    if args.ca1 not in ("1", "2", "3", "4"):
        print(f"❌ --ca1 phải là 1-4 (thấy '{args.ca1}')", file=sys.stderr)
        sys.exit(1)

    # Fill fields
    target["question_label_1"] = args.question_label
    target["question_1"] = args.q1
    target["answer_1"] = a_clean
    target["correct_answer_1"] = args.ca1
    target["explain_vn_1"] = args.evn1
    target["explain_en_1"] = args.een1

    # Đảm bảo Q2-Q5 rỗng (đoạn văn ngắn chỉ có 1 câu)
    for i in range(2, 6):
        for fld in (
            f"question_label_{i}",
            f"question_{i}",
            f"question_image_{i}",
            f"answer_{i}",
            f"correct_answer_{i}",
            f"explain_vn_{i}",
            f"explain_en_{i}",
        ):
            target[fld] = ""

    # Đảm bảo general_image luôn rỗng (đoạn văn ngắn không có screenshot)
    target["general_image"] = ""

    # Write back
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_FIELDNAMES})

    # Summary
    print(f"✅ Đã fill Q1 cho {args.row_id} trong {csv_path}")
    print(f"   question_label_1: {args.question_label}")
    print(f"   question_1: {args.q1[:60]}{'...' if len(args.q1) > 60 else ''}")
    for j, opt in enumerate(opts, 1):
        marker = "  ✓" if str(j) == args.ca1 else ""
        print(f"   ({j}) {opt}{marker}")
    print(f"   correct_answer_1: {args.ca1}")
    evn_preview = args.evn1.replace("\n", " / ")
    print(
        f"   explain_vn_1: {evn_preview[:80]}{'...' if len(evn_preview) > 80 else ''}"
    )


if __name__ == "__main__":
    main()
