# Prompt — Gen bài Đoạn Văn Ngắn (JLPT 短文)

## Cách dùng

Copy prompt bên dưới, thay `{số}` rồi paste vào Claude hoặc Gemini.
SKILL.md chứa workflow + checklist QC. rules/ chứa chi tiết (chủ đề, char range, format question, distractor traps...). Prompt chỉ cần nói **cái gì** và **bao nhiêu**.

---

## Prompt ngắn (khuyên dùng)

```
Đọc .claude/skills/jlpt-reading-short-passage/SKILL.md rồi gen bài đọc hiểu đoạn văn ngắn:
- N5: {số} bài
- N4: {số} bài
- N3: {số} bài
- N2: {số} bài
- N1: {số} bài

Lưu CSV vào sheets/samples_v1.csv. HTML lưu vào assets/html/doan_van_ngan/{LEVEL}_{uuid}.html.
Làm đúng theo SKILL.md — từng bài một, đọc rules/ trước khi gen.

⛔ ĐA DẠNG CHỦ ĐỀ + LABEL — BẮT BUỘC:
1. Đọc rules/rule_doc_hieu.md (rule giáo viên — section 3-5 áp dụng trực tiếp) + rules/content.md (chủ đề per level + char range) + rules/questions.md (label distribution).
2. Scan sheets/samples_v1.csv xem topic + question_label đã dùng.
3. Trong cùng level: KHÔNG trùng topic, dùng ≥ 2 question_label khác nhau (nếu N ≥ 2 bài).
4. Tag **tiếng Anh** từ cột `en` của `rules/topic.json` (vd: family, economics, culture). TUYỆT ĐỐI không tiếng Việt/Nhật.

⛔ CHAR RANGE — Hard Reject phải gen lại:
N1 220–260 (HR<200) | N2 240–290 (HR<200) | N3 220–290 (HR<200) | N4 180–240 (HR<150) | N5 100–160 (HR<80)

⛔ FURIGANA — chỉ cho từ VƯỢT level. Cấm dạng "Ab" (nửa kanji nửa hiragana).
Tra rules/jlpt_kanji.csv. Ưu tiên thay từ đơn giản hơn thay vì rắc furigana.

⛔ ANNOTATION (注) — chỉ N1/N2/N3 khi có thuật ngữ. Giải thích bằng TIẾNG NHẬT đơn giản (やさしい日本語), KHÔNG tiếng Anh/Việt. N4/N5 KHÔNG annotation.

Sau khi gen xong mỗi bài, tự QC checklist trong SKILL.md (HTML + CSV → log PASS/FAIL từng mục). 1 FAIL = sửa → QC lại. Tất cả PASS mới sang bài tiếp.
Điền Q&A vào CSV bằng scripts/fill_qa.py (KHÔNG sửa CSV bằng tay — commas vỡ cột).
Sửa HTML = chạy lại process_html.py --refresh để update text_read + jp_char_count.
Verify cuối: python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py --validate --html-dir assets/html/doan_van_ngan
```

---

## Prompt có thêm ràng buộc (khi cần kiểm soát chất lượng)

```
Đọc .claude/skills/jlpt-reading-short-passage/SKILL.md rồi gen bài đọc hiểu đoạn văn ngắn:
- N5: {số} bài | N4: {số} bài | N3: {số} bài | N2: {số} bài | N1: {số} bài

Lưu CSV vào sheets/samples_v1.csv. HTML lưu vào assets/html/doan_van_ngan/{LEVEL}_{uuid}.html.
Trước khi gen:
1. Đọc rules/rule_doc_hieu.md (rule giáo viên — source-of-truth cho vocab/grammar/distractor)
2. Đọc rules/content.md + rules/vocabulary.md + rules/technical.md + rules/questions.md
3. Đọc rules/jlpt_kanji.csv để tra level kanji khi quyết định furigana
4. Đọc 1-2 sample qua scripts/load_references.py --level {LEVEL} --count 2
5. Scan sheets/samples_v1.csv xem chủ đề + question_label nào đã dùng

⛔ ĐA DẠNG CHỦ ĐỀ + LABEL — BẮT BUỘC:
- Trong cùng level: KHÔNG trùng topic; dùng ≥ 2 question_label khác nhau (nếu N ≥ 2)
- Cross-level: ưu tiên topic chưa xuất hiện
- Tag **tiếng Anh** từ cột `en` của `rules/topic.json` (vd: family, economics, culture). TUYỆT ĐỐI không tiếng Việt/Nhật.

⛔ FURIGANA ZERO-TOLERANCE:
- Mọi kanji vượt level PHẢI có <ruby><rt>
- Cấm dạng "Ab" (媒たい). Chỉ chọn 1 trong 2: full kanji + furigana, HOẶC full hiragana
- Density per level: N5 0–3 | N4 0–4 | N3 0–5 | N2 0–6 | N1 0–7 ruby tags

⛔ ĐÁP ÁN — 4 options ngăn cách \n, KHÔNG prefix "1.", "①", "1)":
✅ "選択肢A\n選択肢B\n選択肢C\n選択肢D"
❌ "1. 選択肢A\n2. 選択肢B\n..."

Yêu cầu chất lượng câu hỏi:
- Question_label dùng prefix `question_` (vd `question_reference`, `question_content_match`)
- Distractor đa dạng ≥ 3 loại bẫy (Detail swap / Scope / Misinterpretation / Part of truth / Mixing). Mỗi distractor PHẢI dùng info thật từ bài, KHÔNG bịa
- Paraphrase: đáp án đúng KHÔNG copy nguyên văn ≥ 4 từ liên tiếp (N1) / 5 từ (N2-N5)
- Câu hỏi answer được TRONG bài (không kiến thức nền)
- Self-solve: tự giải lại từng câu, đáp án phải KHỚP correct_answer_i
- Explanation 3 phần: đáp án đúng (trích bài) + đáp án sai (nêu loại bẫy) + tóm tắt. VN + EN

Sau khi gen xong mỗi bài, BẮT BUỘC tự QC theo checklist trong SKILL.md:
- HTML check (CSS, char count, ruby format, paragraph) + Content (chủ đề, từ vựng level)
- CSV check (label, format đáp án, correct, explain) + Self-solve verify
- 1 FAIL = sửa → refresh CSV (nếu sửa HTML) → QC lại

Lưu ý kỹ thuật:
- Điền Q&A bằng scripts/fill_qa.py (KHÔNG edit CSV tay)
- Refresh CSV sau khi sửa HTML: process_html.py --refresh --file ... --csv ...
- Verify cuối batch: process_html.py --validate --html-dir assets/html/doan_van_ngan
```
