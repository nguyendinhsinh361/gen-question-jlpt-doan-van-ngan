# Prompt — Gen bài Đoạn Văn Ngắn (JLPT 短文)

## Cách dùng

Copy prompt bên dưới, thay `{số}` rồi paste vào Claude hoặc Gemini.

> **🚨 ZERO-TOLERANCE WORKFLOW**: SKILL.md có **5 GATE bắt buộc** (0→1, 1→2, 2→3, 3→4, 4→5). Mỗi gate phải log `GATE X→Y PASSED` mới được sang bước tiếp. **1 mục FAIL = sửa/gen lại → QC TỪ ĐẦU**, đến khi 26/26 PASS mới hoàn thành.

---

## Prompt

```
Đọc .claude/skills/jlpt-reading-short-passage/SKILL.md rồi gen bài đọc hiểu đoạn văn ngắn:
- N5: {số} bài | N4: {số} bài | N3: {số} bài | N2: {số} bài | N1: {số} bài

Lưu CSV: sheets/samples_v1.csv. HTML: assets/html/doan_van_ngan/{LEVEL}_{uuid}.html.

🔒 5 GATE bắt buộc — KHÔNG QUA = KHÔNG SANG BƯỚC TIẾP. Log explicit GATE X→Y PASSED.

═══ BƯỚC 0 — CHUẨN BỊ (1 lần) → GATE 0→1 ═══
Đọc đầy đủ:
- rules/rule_doc_hieu.md (đặc biệt Phần 2.4 thể chia, Phần 5 — 7 loại bẫy: Reversal/Detail Swap/Fabrication/Scope/Mixing + Single-side cho 統合 + Peripheral Source cho N1, Phần 6.1–10.1 per level)
- rules/{content,vocabulary,technical,questions}.md + rules/kanji_jlpt_sensei.csv (2495 kanji)
- Load 2-3 sample: scripts/load_references.py --level {LEVEL} --count 2-3
- Scan sheets/samples_v1.csv để biết topic + label đã dùng
GATE 0→1: tick 6/6 → log "GATE 0→1 PASSED".

═══ BƯỚC 1 — GEN HTML + Q+A → GATE 1→2 ═══
1. _id = {LEVEL}_{uuid32}
2. Tag = **tiếng Anh** từ cột `en` của rules/topic.json (KHÔNG tiếng Việt/Nhật)
3. Gen HTML đúng spec (container 640px, word-break keep-all, <p> thuần, **thể chia đúng level theo Phần 2.4**, furigana chỉ vượt level — cấm "Ab")
4. Gen Q + 4 đáp án (newline \n, KHÔNG prefix "1." "①"); 4 đáp án + câu hỏi cùng thể chia với bài
5. Tạo CSV bằng scripts/process_html.py (KHÔNG sửa CSV tay — commas vỡ cột)
GATE 1→2: tick 5/5 (file tồn tại, CSV row tạo bằng script, _id đúng format, Q+A fill đủ, đã đọc lại HTML) → log "GATE 1→2 PASSED".

═══ BƯỚC 2-3 — QC 26 MỤC → GATE 2→3 + GATE 3→4 ═══
GATE 2→3: cam kết kiểm tra ĐẦY ĐỦ 26 mục, đọc lại HTML+CSV thực tế, log PASS/FAIL với evidence (số ký tự, trích dẫn) → log "GATE 2→3 PASSED".
Đánh giá 26 mục checklist trong SKILL.md (HTML 10 + Content 6 + Q&A 8 + Self-solve verify 2).
**Self-solve mục #25**: tự giải bài từ đầu KHÔNG nhìn correct_answer_1 → KHỚP.
GATE 3→4: liệt kê chính xác mục FAIL với diagnosis cụ thể → log "GATE 3→4 PASSED — fix list: [#x, #y]".

═══ BƯỚC 4-5 — SỬA + LẶP → GATE 4→5 ═══
- Fix HTML → BẮT BUỘC chạy `process_html.py --refresh` để sync CSV
- Fix Q&A → dùng scripts/fill_qa.py (KHÔNG sửa CSV tay)
- ≥ 50% mục FAIL HOẶC self-solve FAIL HOẶC char Hard Reject → **GEN LẠI TỪ ĐẦU** (giữ _id), KHÔNG fix vá
- Quay lại GATE 2→3 → QC TỪ ĐẦU 26 mục (KHÔNG chỉ check mục đã sửa)
- Tối đa 5 vòng. Vẫn FAIL → báo lỗi user, KHÔNG sang bài tiếp
GATE 4→5: 26/26 PASS + đã chạy --validate (no broken ruby) → log "🎉 ALL PASSED (26/26) + GATE 4→5 PASSED" → bài tiếp.

═══ HARD REJECT (gen lại ngay, không thương lượng) ═══
- Char range Hard Reject: N5<80 | N4<150 | N3/N2/N1<200
- <ruby> thiếu <rt> hoặc <rt> rỗng
- Thể chia trộn lẫn (vd N3 vừa だ vừa です trong cùng bài)
- Tag tiếng Việt/Nhật; trùng topic trong cùng level; <2 question_label khác nhau (khi N≥2 bài)
- N4/N5 có 注; annotation 注 dùng tiếng Anh/Việt thay vì やさしい日本語

═══ CUỐI BATCH ═══
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py --validate --html-dir assets/html/doan_van_ngan --csv sheets/samples_v1.csv
```
