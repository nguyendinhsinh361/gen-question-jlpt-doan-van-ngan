# Prompt — Gen bài Đoạn Văn Ngắn (JLPT 短文)

## Cách dùng

Copy prompt bên dưới, thay `{số}` rồi paste vào Claude hoặc Gemini.

> **🚨 ZERO-TOLERANCE QC**: Chỉ cần **1 tiêu chí FAIL** trong checklist QC của SKILL.md → **fix ngay hoặc gen lại** trước khi sang bài tiếp. Không được skip, không được "tạm thời để đó".

---

## Prompt

```
Đọc .claude/skills/jlpt-reading-short-passage/SKILL.md rồi gen bài đọc hiểu đoạn văn ngắn:
- N5: {số} bài | N4: {số} bài | N3: {số} bài | N2: {số} bài | N1: {số} bài

Lưu CSV: sheets/samples_v1.csv. HTML: assets/html/doan_van_ngan/{LEVEL}_{uuid}.html.

═══ BƯỚC 0 — CHUẨN BỊ (1 lần) ═══
1. Đọc rules/rule_doc_hieu.md (rule giáo viên — source-of-truth, 11 phần). Áp dụng đặc biệt:
   - Phần 2.4 (Thể chia 文体の統一): N1/N2/N3 → 普通形 (だ・である); N4/N5 → ます形. Văn bản + câu hỏi + 4 đáp án thống nhất 1 thể. N5 thêm わかち書き (khoảng trắng giữa cụm).
   - Phần 3 (Furigana per level), Phần 4 (8 loại Q), Phần 5 (5 loại bẫy chuẩn).
2. Đọc rules/content.md + vocabulary.md + technical.md + questions.md.
3. Đọc rules/kanji_jlpt_sensei.csv (2495 kanji) để tra level kanji khi quyết định furigana.
4. Load 2-3 sample: scripts/load_references.py --level {LEVEL} --count 2-3.
5. Scan sheets/samples_v1.csv xem topic + question_label đã dùng.

═══ BƯỚC 1→5 — LẶP CHO TỪNG BÀI ═══
1. Gen _id = {LEVEL}_{uuid32}; chọn format chưa/ít dùng + topic + question_label.
2. Tag = **tiếng Anh** từ cột `en` của rules/topic.json (vd: family, economics). TUYỆT ĐỐI không tiếng Việt/Nhật.
3. Gen HTML: container 640px, word-break keep-all, <p> thuần (không <br> trừ N5 letter), furigana chỉ cho từ vượt level (cấm "Ab" — nửa kanji nửa hiragana), thể chia đúng level (Phần 2.4).
4. Gen Q + 4 đáp án (newline \n, KHÔNG prefix "1." "①"); distractor đa dạng ≥ 3 loại bẫy, dùng info THẬT từ bài. Câu hỏi và 4 đáp án cùng thể chia với bài đọc.
5. Tạo CSV row bằng scripts/process_html.py (KHÔNG sửa CSV tay — commas vỡ cột). Hoặc fill Q&A sau bằng scripts/fill_qa.py.

═══ BƯỚC 2 — QC ZERO-TOLERANCE (BẮT BUỘC) ═══
Tự đánh giá checklist trong SKILL.md, log PASS/FAIL từng mục:
- HTML (CSS, char count, ruby <rt> không rỗng, paragraph) + Content (chủ đề, từ vựng đúng level, **thể chia nhất quán**)
- CSV (label, format đáp án, correct_answer, explain VN+EN 3 phần) + Self-solve verify
- **1 FAIL = fix ngay hoặc gen lại → refresh CSV (nếu sửa HTML) → QC lại từ đầu**. CẤM bỏ qua.

═══ HARD REJECT (gen lại ngay, không thương lượng) ═══
- Char range ngoài: N1 220–260 (HR<200) | N2 240–290 (HR<200) | N3 220–290 (HR<200) | N4 180–240 (HR<150) | N5 100–160 (HR<80)
- <ruby> thiếu <rt> hoặc <rt> rỗng
- Thể chia trộn lẫn (vd N3 vừa だ vừa です trong cùng bài)
- Tag tiếng Việt/Nhật thay vì English
- Trong cùng level: trùng topic, hoặc <2 question_label khác nhau (khi N≥2 bài)
- Annotation 注 dùng tiếng Anh/Việt (phải tiếng Nhật やさしい), hoặc N4/N5 có 注

═══ CUỐI BATCH ═══
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py --validate --html-dir assets/html/doan_van_ngan --csv sheets/samples_v1.csv
```
