---
name: jlpt-doan-van-ngan
description: >
  Generate JLPT "đoạn văn ngắn" (short-passage / 短文読解) reading comprehension passages as
  styled HTML files and output CSV training data for AI fine-tuning. Each passage is a short
  Japanese prose text (80–290 characters depending on level) testing content understanding via
  a single multiple-choice question. Skill này bao gồm TOÀN BỘ luồng: gen → QC loop
  (checklist PASS/FAIL) → sửa. Gen từng bài một, kiểm tra đến khi đạt chất lượng mới chuyển
  sang bài tiếp theo. Output chỉ gồm HTML + CSV (không có screenshot PNG).
  Skill này chỉ dành riêng cho dạng "đoạn văn ngắn" (短文読解).
  Use this skill whenever the user wants to: gen bài đoạn văn ngắn, tạo nội dung đoạn văn
  ngắn, generate short-passage reading comprehension, create JLPT 短文 passages,
  produce AI fine-tuning data for the đoạn văn ngắn section of JLPT N1-N5,
  kiểm tra chất lượng, quality check, review bài, QC.
  Also trigger when the user mentions: gen bài đoạn văn ngắn, tạo short passage, generate
  JLPT 短文, short reading passage N1/N2/N3/N4/N5.
---

# JLPT 短文 / Đoạn Văn Ngắn — Workflow

> **Nguyên tắc cốt lõi:**
> 1. **Gen từng bài một** — không batch rồi QC sau
> 2. **Agent tự QC** — đọc lại bài + câu hỏi, tự đánh giá từng mục, log PASS/FAIL
> 3. **1 FAIL = chưa xong** — sửa → QC lại → lặp đến khi ALL PASS
> 4. **KHÔNG có screenshot** — đoạn văn ngắn không cần PNG

## Cấu trúc file

| File | Nội dung | Đọc khi |
|------|----------|---------|
| `SKILL.md` (file này) | Workflow + QC Checklist | Luôn đọc đầu tiên |
| `rules/content.md` | R1 chủ đề + R2 layout/char counts + R7 formats + R8 visual | Gen HTML |
| `rules/vocabulary.md` | R3 từ vựng/ngữ pháp + R4 furigana | Gen HTML + QC |
| `rules/questions.md` | R5 câu hỏi + R6 đáp án/bẫy | Gen Q&A + QC |
| `rules/technical.md` | R9 HTML template + R10 clean HTML + R11 CSV | Gen HTML + CSV |
| `references/html-patterns.md` | Template chi tiết per level + marker conventions | Tra cứu khi gen HTML |
| `references/sample-analysis.md` | Phân tích định lượng data mẫu | Hiểu tần suất pattern |
| `scripts/process_html.py` | Xử lý HTML → CSV + count + validate | Gen CSV + QC |
| `scripts/fill_qa.py` | Điền Q&A vào CSV (quote an toàn) | Sau khi gen Q&A |
| `scripts/load_references.py` | Load sample JSON để calibrate | BƯỚC 0 chuẩn bị |

## Outputs Per Passage

1. **Styled HTML** → `assets/html/doan_van_ngan/{LEVEL}_{uuid}.html`
2. **Clean HTML** → CSV column `text_read` (no attributes, no `<rt>` content)
3. **CSV row** → `sheets/samples_v1.csv` với 1 câu hỏi (question_2-5 empty)

**KHÔNG có screenshot PNG.** CSV column `general_image` luôn `""`.

---

# WORKFLOW

## BƯỚC 0: CHUẨN BỊ (1 lần cho batch)

1. **Đọc `rules/rule_doc_hieu.md`** — **rule chung của giáo viên tiếng Nhật cho TOÀN BỘ phần đọc hiểu** (source-of-truth cho từ vựng/ngữ pháp theo level, kỹ thuật ra câu hỏi, distractor traps). Section 3-5 áp dụng trực tiếp. Section 1-2 (chủ đề + form) chủ yếu cho "tìm thông tin" — tham khảo tinh thần, áp dụng linh hoạt cho prose reading.
2. **Đọc rules skill**: `rules/content.md` + `rules/vocabulary.md` + `rules/technical.md` + `rules/questions.md`
3. **Đọc `rules/jlpt_kanji.csv`** — dùng để tra level từng kanji khi quyết định furigana
4. **Scan `sheets/samples_v1.csv` và `data/doan_van_ngan_n*_clean.json`** — xem format, topic đã dùng → chọn format chưa/ít dùng
5. **Load 2-3 sample calibrate style**:
   ```bash
   python3 .claude/skills/jlpt-reading-short-passage/scripts/load_references.py --level N3 --count 3
   ```
6. **Lập kế hoạch batch**: mỗi bài gán format + topic + question_label khác nhau. Topic chọn **tiếng Anh** từ cột `en` của `rules/topic.json` (đa dạng ≥ 3 category trong batch > 5 bài).

---

## BƯỚC 1→5: LẶP CHO TỪNG BÀI

### BƯỚC 1: GEN HTML + CÂU HỎI

> Đọc: `rules/content.md` + `rules/vocabulary.md` + `rules/technical.md` + `rules/questions.md`
> Tham khảo: `references/html-patterns.md` cho template per level

1. **Gen `_id`** = `{LEVEL}_{uuid.uuid4().hex}` (full 32-char hex)
2. **Chọn format** từ R7 (`rules/content.md`) — 6 formats: essay/anecdote/advice/news brief/letter/diary. Scan `sheets/` + `data/` để chọn format chưa/ít dùng.
3. **Chọn `tag`** (topic) — **tiếng Anh** từ cột `en` của `rules/topic.json`, đa dạng trong batch
4. **Chọn `question_label`** từ R5 — 7 labels, tuân theo distribution per level
5. **Gen HTML** theo rules → save `assets/html/doan_van_ngan/{LEVEL}_{uuid}.html`
   - Container `max-width: 640px; margin: 0 auto`
   - `word-break: keep-all` (đảm bảo xuống dòng sạch ở ranh giới từ)
   - `<p>` thuần, không `<br>` giữa câu (trừ N5 letter)
   - Marker khớp với question_label (nếu reference/fill_in_blank)
   - Furigana chỉ cho từ vượt level (tra `rules/jlpt_kanji.csv`)
6. **Gen câu hỏi + 4 đáp án** theo `rules/questions.md`
   - 4 options ngăn cách `\n`, KHÔNG số thứ tự
   - `correct_answer_1` = integer 1-4
   - Distractor phải có căn cứ trong bài (không bịa)
7. **Tạo CSV row** bằng `process_html.py` (⚠️ **dùng script, KHÔNG sửa CSV tay**):
   ```bash
   python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py \
     --file assets/html/doan_van_ngan/{LEVEL}_{uuid}.html \
     --csv sheets/samples_v1.csv \
     --tag "{topic_english}" \
     --question-label {question_label} \
     --question "Câu hỏi..." \
     --answers "Option1|Option2|Option3|Option4" \
     --correct 2 \
     --explain-vn "Giải thích VN 3 phần..." \
     --explain-en "Explanation EN 3 phần..."
   ```
   Hoặc điền Q&A sau khi row đã tồn tại bằng **fill_qa.py** (an toàn với commas):
   > **⛔ KHÔNG ĐƯỢC sửa CSV bằng tay. Commas trong nội dung (ví dụ `100,000円`, `それは、...`) sẽ làm vỡ cột.**
   > **LUÔN dùng script — tự quote đúng.**
   ```bash
   python3 .claude/skills/jlpt-reading-short-passage/scripts/fill_qa.py \
     --csv sheets/samples_v1.csv --row-id {LEVEL}_{uuid} \
     --question-label {question_label} \
     --q1 "Câu hỏi..." \
     --a1 "Đáp án 1
   Đáp án 2
   Đáp án 3
   Đáp án 4" \
     --ca1 2 \
     --evn1 "..." \
     --een1 "..."
   ```

---

### BƯỚC 2: ⛔ QC — AGENT TỰ ĐÁNH GIÁ CHECKLIST

> **ĐÂY LÀ BƯỚC QUAN TRỌNG NHẤT. KHÔNG ĐƯỢC BỎ QUA.**
>
> Agent phải **đọc lại** file HTML vừa gen + câu hỏi/đáp án trong CSV,
> rồi **tự đánh giá từng mục** bên dưới. Log kết quả theo format:
>
> ```
> QC: {_id}  |  Level: {LEVEL}  |  Label: {question_label}
> ────────────────────────────────
> [ 1] ✅ PASS — Char count (235 chars, range 220-290)
> [ 2] ❌ FAIL — Flow text (found 2x 。<br>)
> [ 3] ✅ PASS — Container CSS (640px, margin auto)
> ...
> ────────────────────────────────
> ⚠️ 1 FAIL → sửa rồi QC lại
> ```
>
> **⛔ KHÔNG ĐƯỢC tự PASS mà không đọc lại nội dung. Phải confirm từng mục.**

---

### BƯỚC 3: ⛔ CHECKLIST — TẤT CẢ PHẢI PASS

> **Quy tắc: 1 FAIL = chưa xong. Sửa → QC lại từ đầu → lặp đến khi ALL PASS.**
> **Tổng: 26 checks ở 3 phần (A HTML, B content, C questions + C2 verify). KHÔNG có PHẦN D ảnh vì không có screenshot.**

#### PHẦN A: HTML (10 checks)

Agent đọc lại file HTML và kiểm tra:

| # | Check | Cách verify | PASS nếu |
|---|-------|-------------|----------|
| 1 | **Char count** | Chạy `process_html.py --count-only --file ...` hoặc `count_body_chars()` | Trong Target Range: N5 100-160, N4 180-240, N3 220-290, N2 240-290, N1 220-260 |
| 2 | **Không Hard Reject** | So với Hard Reject threshold | ≥ N5:80, N4:150, N3/N2/N1:200 |
| 3 | **Flow text** | Tìm `。<br>` trong HTML | Không có `。<br>` nào (trừ N5 letter format) |
| 4 | **Container CSS** | Xem CSS | `max-width: 640px`, `margin: 0 auto`, `word-break: keep-all` (KHÔNG `auto-phrase`) |
| 5 | **`.passage` div** | Xem HTML structure | Có `<div class="passage">` bọc nội dung |
| 6 | **White background** | Xem CSS | `.passage` có `background: white`, body `#f9fafb` |
| 7 | **Furigana format** | Tìm ngoặc `漢字(かんじ)` hoặc `漢字【かんじ】` | Không có — tất cả furigana dùng `<ruby><rt>` |
| 8 | **Ruby có `<rt>` không rỗng** | Xem mọi `<ruby>...</ruby>` | Tất cả đều có `<rt>` chứa furigana **không rỗng** (vd `<ruby>諦<rt>あきら</rt></ruby>`). CẤM `<ruby>諦</ruby>` (thiếu rt) hoặc `<ruby>諦<rt></rt></ruby>` (rt rỗng). Auto-check: `process_html.py --validate` |
| 9 | **Ruby count** | Đếm số `<ruby>` | Trong ngưỡng: N5 0-2, N4 0-4, N3 0-6, N2 0-4, N1 0-2 |
| 10 | **Marker/annotation/source đúng level** | Xem có `<u>`, marker ①, `注`, source line không | Phù hợp level (N4/N5 KHÔNG source, N5 KHÔNG annotation — xem R8) |

#### PHẦN B: NỘI DUNG & TỪ VỰNG (6 checks)

Agent đọc nội dung bài viết và đánh giá:

| # | Check | Cách verify | PASS nếu |
|----|-------|-------------|----------|
| 11 | **Chủ đề đúng level** | Đọc nội dung, đối chiếu `rules/content.md` R1 | Chủ đề phù hợp level (N5: thư/lời nhắn, N1: triết học/phê bình) |
| 12 | **Format đúng level** | Đối chiếu R7 | Format nằm trong 6 formats được phép cho level đó |
| 13 | **Nội dung logic** | Đọc toàn bài | Ý nhất quán, không mâu thuẫn, lập luận rõ |
| 14 | **Không mơ hồ (test 2 cách hiểu)** | Đọc từng câu, thử hiểu theo cách 2 | Chỉ có DUY NHẤT 1 cách hiểu hợp lý |
| 15 | **Từ vựng đúng level** | Đọc từng từ, đối chiếu `rules/vocabulary.md` R3 | Key terms ≤ level, không dùng ngữ pháp vượt level |
| 16 | **Furigana đúng từ (tra CSV)** | Tra từng kanji trong `rules/jlpt_kanji.csv`: có kanji > level → phải có furigana; tất cả kanji ≤ level → không furigana | Mọi từ có kanji vượt level đều có `<ruby><rt>`. Không thừa furigana cho từ đúng level. Không dạng "Ab" (週かん) |

#### PHẦN C: CÂU HỎI & ĐÁP ÁN (8 checks)

Agent đọc câu hỏi + 4 đáp án từ CSV và đánh giá:

| # | Check | Cách verify | PASS nếu |
|----|-------|-------------|----------|
| 17 | **Q1 tồn tại** | Xem CSV | `question_1` có nội dung; `question_2`..`question_5` empty |
| 18 | **question_label đúng intent** | Đối chiếu `rules/questions.md` R5 | Label khớp với dạng câu hỏi (content_match / reference / reason / ...) |
| 19 | **Marker khớp câu hỏi** | So marker trong HTML với câu hỏi | Nếu `question_reference` → HTML có `<u>`/marker; nếu `fill_in_blank` → HTML có `[ ① ]`/`（ 1 ）`; câu hỏi nhắc đúng cụm |
| 20 | **A1 format** | Xem 4 đáp án trong CSV | Đúng 4 options ngăn cách `\n`, không có `1. `/`2. ` prefix. Độ dài tương đương (ratio < 2.0). Thì động từ nhất quán |
| 21 | **A1 correct_answer** | Xem giá trị `correct_answer_1` | Integer 1-4. Scan batch: không lặp cùng vị trí ≥ 3 bài liên tiếp |
| 22 | **A1 paraphrase** | So đáp án đúng với bài gốc | KHÔNG trùng cụm ≥ 4 từ liên tiếp (N3+) hoặc ≥ 6 từ (N4/N5) |
| 23 | **A1 distractor có căn cứ** | Với mỗi đáp án sai: trích được câu/vị trí trong bài để bác bỏ | Không bịa thông tin ngoài bài. Mỗi distractor dùng info/concept từ bài nhưng sai ngữ cảnh |
| 24 | **Explanations 3 phần** | Đọc `explain_vn_1` + `explain_en_1` | Có đủ 3 phần: đáp án đúng (trích vị trí) + đáp án sai (nêu loại bẫy) + tóm tắt. Cả VN và EN đầy đủ |

#### PHẦN C2: VERIFY ĐÁP ÁN (⛔ QUAN TRỌNG NHẤT) — 2 checks

> **Agent tự giải bài từ đầu — KHÔNG nhìn đáp án đã gen.**
> Đây là bước bắt lỗi distractor bịa, câu hỏi ambiguous.

| # | Check | Cách verify | PASS nếu |
|----|-------|-------------|----------|
| 25 | **Tự giải Q1** | Đọc bài + câu hỏi, tự chọn đáp án từ đầu (KHÔNG nhìn `correct_answer_1`) | Kết quả tự chọn KHỚP với `correct_answer_1` trong CSV |
| 26 | **Distractor self-test** | Với TỪNG đáp án sai: trích dẫn chính xác câu/vị trí trong bài dùng để bác bỏ | Mỗi distractor đều trích được câu cụ thể. Không trích được = BỊA → FAIL |

---

### BƯỚC 4: SỬA & LẶP LẠI

> **⛔ Khi sửa HTML, CẬP NHẬT CSV — chạy lại `process_html.py --refresh` để cập nhật `text_read`, `jp_char_count` trong CSV.**
>
> Không có screenshot nên KHÔNG cần chạy lại screenshot script.

| Nếu FAIL | Hành động | Sau đó |
|-----------|-----------|--------|
| #1, #2 (chars) | Bổ sung/cắt nội dung. Nếu Hard Reject → gen lại hoàn toàn | Chạy `--refresh` → QC lại |
| #3 (flow text) | Sửa `<br>` → `</p><p>` | Chạy `--refresh` → QC lại |
| #4, #5, #6 (CSS/structure) | Sửa CSS/structure HTML | Chạy `--refresh` → QC lại |
| #7, #8, #9 (ruby) | Sửa ruby tags | Chạy `--refresh` → QC lại |
| #10 (visual level) | Thêm/bớt annotation/source/marker theo R8 | Chạy `--refresh` → QC lại |
| #11, #12, #13, #14, #15 | Gen lại nội dung (giữ _id) | Chạy `--refresh` → QC lại |
| #16 (furigana tra CSV) | Sửa ruby tags (tra lại `rules/jlpt_kanji.csv`) | Chạy `--refresh` → QC lại |
| #17, #18, #19 (câu hỏi) | Sửa câu hỏi bằng `fill_qa.py` | QC lại (không cần refresh HTML) |
| #20, #21, #22 (đáp án) | Sửa đáp án bằng `fill_qa.py` | QC lại |
| #23 (distractor bịa) | Viết lại distractor dùng info thật từ bài | QC lại |
| #24 (explanation) | Viết lại explain 3 phần đầy đủ | QC lại |
| #25, #26 (self-solve) | Đáp án có thể sai → xem lại bài vs. đáp án | Sửa đáp án hoặc bài. QC lại |

**Lệnh refresh CSV sau khi sửa HTML:**
```bash
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py \
  --refresh \
  --file assets/html/doan_van_ngan/{LEVEL}_{uuid}.html \
  --csv sheets/samples_v1.csv
```

> **Vòng lặp: sửa → refresh CSV (nếu sửa HTML) → quay lại BƯỚC 2 (QC lại TẤT CẢ) → nếu còn FAIL thì lặp lại.**
> **Tối đa 5 vòng. Sau 5 vòng vẫn FAIL → báo lỗi cho user, KHÔNG bỏ qua.**

---

### BƯỚC 5: ✅ HOÀN THÀNH → BÀI TIẾP THEO

Chỉ khi **TẤT CẢ 26 checks PASS** → log:
```
🎉 ALL PASSED (26/26) — {_id} hoàn thành
```
→ Chuyển sang bài tiếp theo (quay lại BƯỚC 1).

---

## BƯỚC CUỐI: VERIFY BATCH (sau khi gen xong TẤT CẢ bài)

Sau khi hoàn thành toàn bộ batch, chạy verify toàn bộ:

```bash
# 1. Validate tất cả file HTML (char count + broken ruby)
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py \
  --validate --html-dir assets/html/doan_van_ngan

# 2. Đếm số rows trong CSV = đúng số bài đã gen
python3 -c "
import csv
with open('sheets/samples_v1.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
print(f'Total rows: {len(rows)}')
for level in ['N1','N2','N3','N4','N5']:
    n = sum(1 for r in rows if r.get('level') == level)
    print(f'  {level}: {n}')
"

# 3. (Optional) Merge multi-level CSV nếu có nhiều file
# (hầu hết use case chỉ có 1 file samples_v1.csv)
```

### Batch-level checklist

- [ ] Mỗi bài có `_id` unique, đúng format `{LEVEL}_{uuid}`
- [ ] `kind` = `đoạn văn ngắn` trong tất cả rows
- [ ] `general_image` = `""` (empty) — KHÔNG có PNG
- [ ] `general_audio` = `""` (empty)
- [ ] Char count trong Target Range cho mọi bài (hoặc đã gen lại)
- [ ] Không bài nào dưới Hard Reject threshold
- [ ] Furigana chỉ cho từ vượt level, không dạng "Ab", mọi `<ruby>` có `<rt>`
- [ ] Ruby tags count ≤ expected (N5: 2, N4: 4, N3: 6, N2: 4, N1: 2)
- [ ] Mỗi bài có đúng 1 câu hỏi (`question_2` → `question_5` empty)
- [ ] `question_label_1` đa dạng (≥ 2 label khác nhau nếu batch > 3 bài; ≥ 3 nếu batch > 5)
- [ ] Mỗi câu hỏi có 4 đáp án ngăn cách `\n` trong `answer_1` (KHÔNG số thứ tự)
- [ ] `correct_answer_1` phân bố đều 1-4 trong batch (không lặp ≥ 3 bài liên tiếp)
- [ ] Distractor dùng info từ bài (không bịa)
- [ ] `explain_vn_1` + `explain_en_1` đủ 3 phần
- [ ] Marker trong text khớp câu hỏi (nếu có `<u>`, `[ ① ]`, ...)
- [ ] `text_read` clean — không attribute, không class, không `<rt>` content
- [ ] `<p>` thuần, không `<br>` giữa câu (trừ N5 letter)
- [ ] Annotation (注) giải thích bằng **tiếng Nhật đơn giản**, KHÔNG tiếng Anh/Việt
- [ ] Trong batch, tag đa dạng ≥ 3 category (nếu batch > 5)

---

## Reference Data & Samples

Data mẫu có sẵn trong `data/`:

| Level | File | Samples |
|-------|------|---------|
| N1 | `doan_van_ngan_n1_clean.json` | 104 |
| N2 | `doan_van_ngan_n2_clean.json` | 205 |
| N3 | `doan_van_ngan_n3_clean.json` | 140 |
| N4 | `doan_van_ngan_n4_clean.json` | 124 |
| N5 | `doan_van_ngan_n5_clean.json` | 105 |

Load bằng:
```bash
# Stats tất cả levels
python3 .claude/skills/jlpt-reading-short-passage/scripts/load_references.py --stats

# 3 random samples N3
python3 .claude/skills/jlpt-reading-short-passage/scripts/load_references.py --level N3 --count 3
```

**LƯU Ý khi đọc data gốc**:
- Data gốc DÙNG `<br>` nhiều — thói quen xấu. Output HTML skill KHÔNG theo.
- Data gốc có `<span>` bọc paragraph — output KHÔNG cần.
- Data gốc N4 rắc ruby trên từ đúng level — output KHÔNG theo.

Đọc sample để học **nội dung/chủ đề/question pattern**, KHÔNG bắt chước styling xấu của data gốc.

Chi tiết phân tích từng level xem `references/sample-analysis.md`.

---

## Cảnh báo bảo mật dữ liệu

> **🚫 KHÔNG ĐƯỢC GHI VÀO THƯ MỤC `rules/`** — `rules/question_sheet.csv`, `rules/topic.json`, `rules/jlpt_kanji.csv`, `rules/rule_doc_hieu.md` là file tham chiếu, chỉ đọc. Mọi dữ liệu gen phải ghi vào `sheets/samples_v1.csv`.
