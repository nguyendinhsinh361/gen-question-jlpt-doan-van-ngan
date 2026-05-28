# Prompt — Gen bài Đoạn Văn Ngắn (JLPT 短文)

Copy prompt bên dưới, thay `{số}` rồi paste vào Claude hoặc Gemini.

## Prompt

```
Đọc .claude/skills/jlpt-reading-short-passage/SKILL.md và tuân thủ đầy đủ workflow + 5 GATE.

Gen bài đọc hiểu đoạn văn ngắn:
- N5: {số} | N4: {số} | N3: {số} | N2: {số} | N1: {số}

Lưu CSV: sheets/samples_v1.csv
Lưu HTML: assets/html/doan_van_ngan/{LEVEL}_{uuid}.html
```

---

## Prompt QC hậu kỳ

Chạy QC trên CSV đã gen — auto-check scripts + LLM review + auto-fix tối đa 3 vòng.

```
Đọc .claude/skills/jlpt-reading-short-passage-post-qc/SKILL.md và chạy QC đầy đủ theo workflow.

CSV cần QC: sheets/samples_v1.csv

Phạm vi (chọn 1):
- ALL: toàn bộ CSV
- LEVEL: chỉ rows có level = {N1|N2|N3|N4|N5}
- ID: chỉ row có _id = {LEVEL}_{uuid}

Quy trình BẮT BUỘC:
1. BƯỚC 1 — Auto-check: chạy post_qc.py + check_furigana + check_spacing + check_csv_fields + check_answer_punctuation
2. BƯỚC 2 — LLM review: đánh giá L1-L16 cho từng row (L1 thể chia, L2 paraphrase, L3 distractor, L4 key term, L5 marker, L6 answer verify, L7 topic, L8 explain, L9 trap classifier, L10-L12 đặc trưng, L14-L16 nhất quán/固有名詞/注)
3. BƯỚC 3 — Cross-batch: B1-B5 (topic diversity, label diversity, content similarity, label distribution %, (中略) rate)
4. BƯỚC 4 — Auto-fix: row FAIL → sửa tối thiểu phần lỗi (KHÔNG gen lại toàn bộ), lặp tối đa 3 vòng

Báo cáo theo format trong SKILL.md (PASS/FAIL từng L item + cross-batch + tổng kết).
```

---

## Prompt với topic chỉ định

Chỉ định topic cho từng level. Topic dùng tiếng Anh từ cột `en` của `rules/topic.json` (vd: `family`, `education`, `psychology`, `philosophy`).

```
Đọc .claude/skills/jlpt-reading-short-passage/SKILL.md và tuân thủ đầy đủ workflow + 5 GATE.

Gen bài đọc hiểu đoạn văn ngắn với số bài + topic chỉ định cho từng level:
- N5: 3 bài | topic: family
- N4: 3 bài | topic: school
- N3: 5 bài | topic: environment
- N2: 2 bài | topic: psychology
- N1: 3 bài | topic: education

Quy tắc:
- Topic PHẢI có trong cột `en` của `rules/topic.json` — kiểm tra trước, không có → DỪNG báo user.
- CSV field `tag` của mỗi row = topic của level đó.
- Nếu nhiều bài cùng level → giữ chung topic NHƯNG mỗi bài khác format/góc nhìn.

Lưu CSV: sheets/samples_v1.csv
Lưu HTML: assets/html/doan_van_ngan/{LEVEL}_{uuid}.html
```
