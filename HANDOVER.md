# HANDOVER — Đoạn Văn Ngắn Skill

Tài liệu giao/nhận cho skill **jlpt-reading-short-passage**. Đọc file này trước khi chạy batch gen hoặc khi bàn giao cho team mới.

## 1. Mục đích

Gen dữ liệu huấn luyện AI cho **dạng "đoạn văn ngắn"** (短文読解) của JLPT N1-N5. Mỗi bài gồm:

- 1 đoạn văn Nhật ngắn (80–290 ký tự tuỳ level)
- 1 câu hỏi multiple-choice với 4 đáp án, 1 đáp án đúng
- Giải thích tiếng Việt + tiếng Anh

Khác với skill "tìm thông tin" (情報検索): **không cần screenshot PNG**, chỉ HTML + Clean HTML + CSV.

## 2. Cấu trúc project

```
gen-question-doan-van-ngan/
├── data/                                    # Sample JSON thực tế từ đề JLPT cũ
│   ├── doan_van_ngan_n1_clean.json          # 104 samples
│   ├── doan_van_ngan_n2_clean.json          # 205 samples
│   ├── doan_van_ngan_n3_clean.json          # 140 samples
│   ├── doan_van_ngan_n4_clean.json          # 124 samples
│   └── doan_van_ngan_n5_clean.json          # 105 samples
├── .claude/skills/jlpt-reading-short-passage/
│   ├── SKILL.md                             # Main skill definition
│   ├── scripts/
│   │   ├── process_html.py                  # Count chars + clean HTML + CSV upsert
│   │   └── load_references.py               # Pretty-print sample JSON cho gen agent
│   └── references/
│       ├── sample-analysis.md               # Phân tích data patterns theo level
│       └── html-patterns.md                 # HTML template per level + markers
├── .gemini/skills/jlpt-reading-short-passage/   # Mirror identical của .claude/
├── assets/html/doan_van_ngan/               # Output HTML files (created at runtime)
├── sheets/                                   # Output CSV files (created at runtime)
├── HANDOVER.md                               # (file này)
└── PROMPTS.md                                # Prompt templates cho gen agent
```

## 3. Pipeline chuẩn

### Bước 1 — Load references (để calibrate style)

```bash
cd /path/to/gen-question-doan-van-ngan
python3 .claude/skills/jlpt-reading-short-passage/scripts/load_references.py --stats
python3 .claude/skills/jlpt-reading-short-passage/scripts/load_references.py --level N3 --count 3 --seed 42
```

Gen agent đọc 2–3 sample cùng level để học độ dài, chủ đề, cấu trúc câu hỏi. **KHÔNG bắt chước styling của data gốc** (data gốc dùng `<br>` và `<ruby>` sai quy tắc — xem `references/sample-analysis.md`).

### Bước 2 — Gen HTML từ LLM

LLM dùng prompt trong `PROMPTS.md` (template per level) để gen ra:
1. HTML file đầy đủ (có `<!DOCTYPE>`, Noto Sans JP CSS)
2. 1 câu hỏi, 4 đáp án, đáp án đúng
3. Giải thích VN + EN

### Bước 3 — Save HTML

Tên file: `{LEVEL}_{uuid4().hex}.html`. Ví dụ: `N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5.html`

```python
import uuid
filename = f"N3_{uuid.uuid4().hex}.html"
# → N3_abc123...
```

Save vào `assets/html/doan_van_ngan/`.

### Bước 4 — Process + commit CSV

```bash
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py \
    --file assets/html/doan_van_ngan/N3_abc123...html \
    --csv sheets/samples_v1.csv \
    --tag "nhật ký" \
    --question-label question_content_match \
    --question "..." \
    --answers "A|B|C|D" \
    --correct 2 \
    --explain-vn "..." \
    --explain-en "..."
```

Script sẽ:
- Count `jp_char_count` từ full HTML (skip `<rt>`, whitespace)
- Extract clean HTML (bỏ attribute, collapse whitespace, bỏ `<rt>` content)
- Hard-reject nếu dưới threshold (N1-N3 < 200, N4 < 150, N5 < 80) — không commit CSV
- Cảnh báo nếu dưới Target Range
- Upsert row vào CSV (45 columns) theo `_id` = filename

### Bước 5 — Validate batch

```bash
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py \
    --validate --html-dir assets/html/doan_van_ngan
```

Exit code 0 = tất cả pass; 1 = có file fail (UNDER_TARGET / HARD_REJECT).

### Bước 6 — Refresh sau khi edit HTML

Nếu sửa HTML file thủ công, refresh các column `jp_char_count` + `text_read`:

```bash
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py \
    --refresh --html-dir assets/html/doan_van_ngan --csv sheets/samples_v1.csv
```

## 4. Target ranges (BẮT BUỘC)

| Level | Target Range | Hard Reject | Số câu/bài |
|-------|--------------|-------------|-----------|
| N1    | 220–260      | < 200       | 1         |
| N2    | 240–290      | < 200       | 1         |
| N3    | 220–290      | < 200       | 1         |
| N4    | 180–240      | < 150       | 1         |
| N5    | 100–160      | < 80        | 1         |

## 5. CSV Schema (45 columns, từ `question_sheet.csv`)

Các column quan trọng đối với skill này:

| Column | Value |
|--------|-------|
| `_id`  | `{LEVEL}_{uuid32hex}` |
| `level` | N1/N2/N3/N4/N5 |
| `tag`  | Topic (nhật ký, kinh tế, xã hội, …) |
| `jp_char_count` | Từ `count_body_chars()` trên full HTML |
| `kind` | `đoạn văn ngắn` (fixed) |
| `general_audio` | "" |
| `general_image` | **""** (empty — khác tìm thông tin) |
| `text_read` | Clean HTML (no attributes, no `<rt>`) |
| `text_read_vn` / `text_read_en` | "" |
| `question_label_1` | content_match / reason_explanation / reference / meaning_interpretation / content_mismatch / author_opinion / fill_in_the_blank |
| `question_1` | Câu hỏi tiếng Nhật |
| `question_image_1` | "" |
| `answer_1` | 4 options ngăn cách `\n`: `1. A\n2. B\n3. C\n4. D` |
| `correct_answer_1` | Số 1–4 |
| `explain_vn_1` / `explain_en_1` | Giải thích |
| `question_2`..`question_5` | **""** (empty — đoạn văn ngắn chỉ 1 câu) |

## 6. Quality Gates

Trước khi coi 1 batch là xong:

- [ ] 100% file qua Hard Reject threshold
- [ ] ≥ 80% file nằm trong Target Range (phần còn lại UNDER/OVER < 30 chars)
- [ ] Batch ≥ 5 bài có ≥ 3 `question_label` khác nhau
- [ ] Batch ≥ 5 bài có ≥ 3 `tag` khác nhau
- [ ] 0 file có furigana dạng "Ab" (kiểm tra grep `[漢字]+[ひらがな]+<rt>`)
- [ ] 100% file có `general_image = ""` (enforce trong `process_html.py`)
- [ ] 100% row có `kind = "đoạn văn ngắn"`
- [ ] 0 row có `question_2`–`question_5` non-empty
- [ ] Mỗi row có 4 đáp án trong `answer_1`, 1 `correct_answer_1` là số 1–4
- [ ] `explain_vn_1` + `explain_en_1` đều non-empty

## 7. Edge cases & pitfalls

1. **Data gốc có `<br>` rải rác** — KHÔNG bắt chước. Output dùng `<p>` thuần.
2. **Data gốc rắc `<ruby>` bừa bãi** (N4 có 12%) — KHÔNG bắt chước. Chỉ furigana cho từ vượt level.
3. **Dạng "Ab" (週かん, 友だち)** — tuyệt đối không. Xem SKILL.md.
4. **Source line chỉ cho N1-N3** — N4/N5 không có. Fake author/title.
5. **Annotation 注 chỉ cho N1-N3** — N5 không có (0% data).
6. **N5 letter format** — ngoại lệ được phép `<br>` + full-width `　`.
7. **Correct index conversion** — data gốc JSON `correctAnswer` là **0-based**, CSV `correct_answer_1` là **1-based**. `load_references.py` đã tự động hiển thị cả hai.

## 8. Tương lai (Phase 2+)

- Phase 2: mirror skill cho "đoạn văn vừa" (N1-N5), "đoạn văn dài" (N1/N3), "đọc hiểu chủ đề" (N1/N2), "đọc hiểu tổng hợp" (N1/N2) — xem `../PLAN_5_DANG_DOC_HIEU.md`.
- Post-pipeline: bổ sung `text_read_vn` / `text_read_en` nếu cần bản dịch (hiện đang empty).
- CSV consolidation: merge CSVs của 5 skill thành 1 `sheets/master.csv` để train.

## 9. Liên hệ

- Skill owner: Nguyễn Đình Sinh <sinhnd@eupgroup.net>
- Reference: `../gen-question-jlpt/` (skill tìm thông tin, Phase 0)
- Master plan: `../PLAN_5_DANG_DOC_HIEU.md`
