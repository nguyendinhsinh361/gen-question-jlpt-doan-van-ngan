# jlpt-short-passage-post-qc

## Mô tả
QC hậu kỳ cho CSV output của dạng đoạn văn ngắn (短文). Dùng khi muốn kiểm tra lại chất lượng sau khi gen xong.

## Trigger
- "QC lại đoạn văn ngắn"
- "kiểm tra CSV đoạn văn ngắn"
- "post-QC short passage"

---

## QUY TRÌNH POST-QC

### BƯỚC 1: AUTO-CHECK (chạy script)

Chạy post_qc.py chính:
```bash
python3 .claude/skills/jlpt-reading-short-passage-post-qc/scripts/post_qc.py \
  --csv sheets/samples_v1.csv \
  --rules-dir rules/ \
  --verbose
```

Chạy thêm các script kiểm tra bổ sung:
```bash
python3 .claude/skills/jlpt-reading-short-passage/scripts/check_furigana.py --html-dir assets/html/doan_van_ngan --level-from-filename --csv rules/kanji_jlpt_sensei.csv
python3 .claude/skills/jlpt-reading-short-passage/scripts/check_spacing.py --html-dir assets/html/doan_van_ngan --level-from-filename
python3 .claude/skills/jlpt-reading-short-passage/scripts/check_csv_fields.py --csv sheets/samples_v1.csv --kind short
python3 .claude/skills/jlpt-reading-short-passage/scripts/check_answer_punctuation.py --csv sheets/samples_v1.csv
```

Thu thập tất cả kết quả từ các script trên. Nếu có lỗi HARD REJECT, dừng lại và báo cáo ngay.

---

### BƯỚC 2: LLM REVIEW (agent đọc từng row)

Với mỗi row trong CSV, agent đọc `text_read` + `question` + `answer` và kiểm tra các tiêu chí sau:

#### L1: Thể chia nhất quán (文体の統一)
- N1-N3: dùng 普通形 (だ/である). Cả bài + câu hỏi + 4 đáp án phải cùng thể.
- N4-N5: dùng ます形.
- **ĐẶC BIỆT**: không trộn です/ます trong Q/A của N1-N3.

#### L2: Paraphrase quality
- Đáp án đúng KHÔNG copy nguyên từ bài đọc.
- N3 trở lên: cụm ≥4 từ liên tiếp giống bài gốc = **FAIL**.
- N4-N5: cụm ≥6 từ liên tiếp giống bài gốc = **FAIL**.

#### L3: Distractor validity
- 3 đáp án sai dùng thông tin từ bài nhưng sai ngữ cảnh.
- **REJECT** nếu đáp án sai bịa thông tin không có trong bài hoặc sai hiển nhiên (ai đọc cũng biết sai).

#### L4: Key term level
- Từ then chốt (cần để trả lời câu hỏi) phải ≤ level mục tiêu.
- Từ vượt level chỉ được phép xuất hiện ở phần bối cảnh + phải có furigana.

#### L5: Marker-question consistency
- Nếu `question_label` là `question_reference` hoặc `question_meaning_interpretation` → HTML phải có `<u>` tag tương ứng đánh dấu từ/cụm từ được hỏi.
- Nếu `question_fill_in_the_blank` → phải có `[ ① ]` hoặc `[　　]` trong bài.

#### L6: Correct answer verification
- Đọc bài, xác nhận đáp án đúng **THỰC SỰ** đúng.
- Xác nhận 3 đáp án sai **THỰC SỰ** sai (không thể chọn được).

#### L7: Topic-level appropriateness
- Chủ đề phù hợp level:
  - N5: thư cá nhân, nhật ký, thông báo đơn giản
  - N4: email công việc, hướng dẫn, thông báo
  - N3: bài báo đơn giản, blog, review
  - N2: bài luận, bình luận xã hội, khoa học phổ thông
  - N1: triết học, phê bình văn học, nghiên cứu chuyên sâu

#### L8: Explanation quality
- `explain_vn` và `explain_en` có đầy đủ.
- Giải thích cả đáp án đúng (tại sao đúng) lẫn đáp án sai (tại sao sai).

#### L9: Trap-type classification — 5 bẫy chuẩn

Với MỖI distractor (3 đáp án sai), agent PHẢI phân loại vào 1 trong 5 loại bẫy chuẩn:

| Bẫy | Mô tả | Dấu hiệu |
|-----|-------|----------|
| **Reversal** ❌ | Đảo ngược ý nghĩa/kết luận từ bài | Bài: "Aによって元気になった" → Bẫy: "Aの後で体が重くなった" |
| **Detail Swap** 🔄 | Gán thông tin đúng vào ngữ cảnh sai (đối tượng/thời điểm/địa điểm khác) | Bài: "Aは嵐山, Bは金閣寺" → Bẫy: "Aは金閣寺" |
| **Fabrication** 🎭 | Thêm thông tin KHÔNG có trong bài | Bài không nói X → Bẫy: "XだからY" |
| **Scope** 📐 | Quá RỘNG (over-generalization) hoặc quá HẸP | Bài: "金閣寺で写真" → Bẫy rộng: "京都で写真" / Bẫy hẹp: "池のそばで写真" |
| **Mixing** 🧩 | Kết hợp 2 thông tin đúng riêng lẻ thành ý sai | A đúng + B đúng → Bẫy: "AだからB" (không liên quan) |

**Quy tắc**:
- 3 distractor PHẢI dùng **≥ 3 loại bẫy khác nhau** (không lặp 3 lần cùng loại)
- Mỗi distractor PHẢI dùng info THẬT từ bài (trừ Fabrication có thể cận-context)
- Distractor "generic wrong" không khớp 1 trong 5 loại → **FAIL** (cần redesign)

#### L10: 短文 N1 — Bẫy đặc trưng

N1 短文 yêu cầu 4 loại bẫy nâng cao (kèm 5 chuẩn ở L9):

- **Surface vs depth**: distractor có sentence rep gần đúng nhưng diễn giải nông (vs thesis sâu)
- **Reversal logic**: đảo ngược premise/conclusion (vd: "A → B" thành "B → A")
- **Concept substitution**: thay khái niệm cốt lõi (vd: 独創性 ↔ 創造性) — gần nghĩa nhưng sai nuance
- **Peripheral Source** (📎): dùng nội dung từ 注 thay vì văn bản chính làm câu trả lời cho thesis Q

#### L11: 短文 N2 — Bẫy đặc trưng

- **Concede trap**: lấy "確かに…" "もちろん…" (ý nhượng bộ) làm đáp án — sai vì đây là ý đối lập tác giả nêu để bác bỏ
- **Fact vs opinion**: nhầm "sự thật" (fact) với "quan điểm tác giả" (opinion)
- **author_opinion phân bổ ~45%** ở N2 短文 — nếu batch không có Q nào author_opinion ở N2 → cảnh báo

#### L12: 短文 — Phân bổ question_label per level (teacher %)

- N2: author_opinion ~45%, reference ~25%, reason ~20%, content_match ~10%
- N1: fill_in ~40%, author_opinion ~25%, meaning_interpretation ~20%, reference ~15%
- content_match HẦU NHƯ KHÔNG có ở N2 短文 — flag nếu xuất hiện nhiều
- meaning_interpretation CHỈ ở N1 短文 — flag nếu xuất hiện ở N2 trở xuống

#### L14: 「」 vs `<u>` consistency (Phần 2.1)

- Nếu text_read dùng `<u>...</u>` để đánh dấu cụm được hỏi → câu hỏi PHẢI dùng `<u>...</u>` (KHÔNG bao quanh `「」`)
- Nếu text_read dùng `「...」` (ngoặc kép Nhật) → câu hỏi cũng dùng `「...」`
- Auto-check: `check_quotes_underline_consistency` đã enforce — agent confirm
- KHÔNG được: text_read `<u>X</u>` mà question stem `「X」` → FAIL

#### L15: 固有名詞 (Tên riêng) — Furigana

- Tên người và địa danh BẮT BUỘC có furigana ở **mọi level** nếu cách đọc không hiển nhiên
- Ví dụ: `金閣寺(きんかくじ)` ở N4 → cần furigana dù 金/閣 là N2/N3
- Ngoại lệ: tên phổ biến đã học không cần (田中, 山田, 佐藤 ở N5-N4)
- Agent kiểm tên người (Surname + Given) và địa danh — flag nếu thiếu furigana

#### L16: 注 KHÔNG được hỏi trực tiếp (Phần 2.3)

- 注 (annotation) chỉ giải thích bối cảnh — câu hỏi KHÔNG được hỏi nội dung trực tiếp về 注
- Vi dụ SAI: 注1 nói `XXX: 〜という考え方` → Q hỏi "XXX là gì?" và đáp án copy nguyên 注 → FAIL
- Distractor N1 长文 dùng nội dung 注 làm đáp án sai = **Peripheral Source trap** (đúng/được phép)
- Agent confirm: question chính KHÔNG hỏi trực tiếp content trong 注


---

### BƯỚC 3: CROSS-BATCH (script đã check, agent review)

#### B1: Topic diversity
- Các bài trong cùng level không được trùng tag/chủ đề.
- Agent kiểm tra xem các chủ đề có đa dạng không.

#### B2: Question label diversity
- Các câu hỏi trong cùng level phải dùng nhiều loại `question_label` khác nhau.
- Tối thiểu 2 loại nếu ≤5 câu, 3 loại nếu >5 câu.

#### B3: Content similarity
- Agent đọc `text_read` của các bài cùng level.
- Flag nếu nội dung giống nhau (cùng chủ đề + cùng góc nhìn + cùng luận điểm).

#### B4: Question label distribution per level (teacher %)

Agent đếm phân bố `question_label` trong batch cùng level và so với teacher distribution. Flag nếu lệch > 20%:

**短文**:
- N2: author_opinion ~45%, reference ~25%, reason ~20%, content_match ~10%
- N1: fill_in ~40%, author_opinion ~25%, meaning ~20%, reference ~15%

**中文**:
- N2: Q2 author_opinion ~60%
- N1: combo fill×fill ~25%

**長文 N1**: Q1 ref ~38%, Q2 reason ~38%, Q3 author_opinion ~60%

**主張 N1**: Q1 meaning ~38%, Q3 author_opinion ~72%, fill_in HIẾM ~10-15%

**統合 N1**: 関係 ~10-15% (KHÔNG có ở N2)

Nếu batch > 5 bài cùng level và lệch teacher > 20% → cảnh báo (không phải FAIL, nhưng review).

#### B5: (中略) presence rate per dạng-level

Auto-check: `check_chuuryaku_rate` đã enforce — agent xem output.

Teacher kỳ vọng:
- **長文 N1**: (中略) ~30-35% bài
- **主張 N1**: (中略) ~40-45% bài
- **主張 N2**: (中略) ~28-35% bài
- **長文 N3 / 統合 / 短文 / 中文**: (中略) hiếm hoặc không có

Nếu batch ≥ 3 bài cùng level lệch > 50% so với teacher → cảnh báo (rất ít hoặc quá nhiều (中略)).

---

### BÁO CÁO

Log kết quả per row theo format:

```
Row {n} [{level}] {_id}:
  AUTO-CHECK: PASS/FAIL + chi tiết lỗi từ script
  L1 文体: PASS/FAIL + chi tiết
  L2 Paraphrase: PASS/FAIL + chi tiết
  L3 Distractor: PASS/FAIL + chi tiết
  L4 Key term: PASS/FAIL + chi tiết
  L5 Marker: PASS/FAIL + chi tiết
  L6 Answer: PASS/FAIL + chi tiết
  L7 Topic: PASS/FAIL + chi tiết
  L8 Explain: PASS/FAIL + chi tiết
```

Tổng hợp cuối:
```
TỔNG KẾT:
  Total: X rows
  PASS: Y rows
  FAIL: Z rows
  Cross-batch issues: N issues
```

---

### BƯỚC 4: AUTO-RETRY — SỬA LỖI (tối đa 3 lần)

> **QUY TẮC BẮT BUỘC**: Nếu có bất kỳ row nào FAIL ở Bước 1 (auto-check) hoặc Bước 2 (LLM review), agent PHẢI tự động sửa row đó. KHÔNG được dừng lại chỉ để báo lỗi. KHÔNG gen lại toàn bộ nội dung — chỉ chỉnh sửa phần vi phạm.

#### Quy trình sửa lỗi:

1. **Xác định lỗi cụ thể**: Thu thập danh sách row bị lỗi, lỗi ở check nào, vi phạm rule gì, ở field nào.

2. **Sửa chính xác phần lỗi** (KHÔNG viết lại toàn bộ):

   | Loại lỗi | Cách sửa |
   |-----------|----------|
   | **Spacing** (full-width/half-width) | Sửa đúng ký tự space trong field bị lỗi. N5: `text_read` dùng U+3000, các field khác dùng half-width. N1-N4: tất cả dùng half-width. |
   | **Char count** ngoài range | Cắt bớt hoặc thêm câu vào `text_read` sao cho vừa range, giữ nguyên ý nghĩa và logic. |
   | **Ruby/Furigana** sai | Sửa tag `<ruby><rt>` theo Rules A/B/C trong `rules/vocabulary.md`. |
   | **文体 không nhất quán** | Chuyển đổi đúng thể: N1-N3 → 普通形 (だ/である), N4-N5 → ます形. Sửa cả bài + câu hỏi + đáp án. |
   | **Paraphrase vi phạm** | Diễn đạt lại đáp án đúng — thay từ đồng nghĩa, đổi cấu trúc câu. Giữ nguyên ý nghĩa. |
   | **Distractor kém** | Sửa đáp án sai: dùng thông tin có trong bài nhưng sai ngữ cảnh/quan hệ. Không bịa thông tin mới. |
   | **Key term vượt level** | Thay từ khó bằng từ cùng nghĩa ở level phù hợp, hoặc thêm furigana nếu từ ở phần bối cảnh. |
   | **Marker-question mismatch** | Thêm/sửa `<u>` tag hoặc `[ ① ]` trong HTML cho đúng với `question_label`. |
   | **Đáp án đúng sai** | Sửa `correct_answer` hoặc sửa nội dung đáp án/bài đọc cho khớp. |
   | **Tag không có trong topic.json** | Đổi tag sang tag gần nghĩa nhất có trong `rules/topic.json`. |
   | **Answer position skewed** | Đổi vị trí `correct_answer` (1→3, 2→4, v.v.) và xáo trộn thứ tự đáp án tương ứng. |
   | **Label diversity thấp** | Đổi loại câu hỏi (`question_label`) của 1-2 row và sửa lại câu hỏi + đáp án cho phù hợp label mới. |
   | **Explanation thiếu** | Bổ sung `explain_vn`/`explain_en` — giải thích tại sao đáp án đúng đúng và từng đáp án sai sai. |

3. **Cập nhật CSV**: Ghi lại row đã sửa vào file CSV (giữ nguyên `_id`, `level`).

4. **Chạy lại QC**: Chạy lại post_qc.py trên toàn bộ CSV:
   ```bash
   python3 .claude/skills/jlpt-reading-short-passage-post-qc/scripts/post_qc.py --csv sheets/samples_v1.csv --verbose
   ```
   Đồng thời chạy lại LLM review (Bước 2) cho các row vừa sửa.

5. **Lặp lại**: Nếu vẫn FAIL → đọc lỗi mới, sửa tiếp. **Tối đa 3 vòng sửa cho mỗi row.**

6. **Dừng khi**:
   - Tất cả row PASS → báo cáo thành công ✅
   - Đã sửa 3 vòng mà vẫn FAIL → báo cáo row nào không thể sửa và lỗi cụ thể ❌

#### Nguyên tắc sửa:
- **Sửa tối thiểu**: Chỉ thay đổi phần vi phạm, giữ nguyên tối đa nội dung gốc.
- **Đọc lại rules**: Trước khi sửa, đọc lại rule liên quan trong `rules/` và `.claude/skills/jlpt-reading-short-passage/SKILL.md`.
- **Mỗi vòng đọc lại lỗi**: Tránh sửa xong lỗi A lại tạo ra lỗi B.
- **KHÔNG gen lại row đã PASS** — chỉ sửa row FAIL.
- **Giữ tính nhất quán**: Nếu sửa `text_read`, kiểm tra lại câu hỏi + đáp án vẫn đúng. Nếu sửa đáp án, kiểm tra lại `explain` vẫn khớp.

---

### BÁO CÁO CUỐI CÙNG

```
TỔNG KẾT POST-QC:
  Total rows: X
  PASS (lần đầu): Y rows
  PASS (sau sửa): Z rows
  FAIL (không thể sửa): W rows
  Số vòng sửa đã dùng: R
  Cross-batch issues còn lại: N
```

Nếu có row FAIL sau 3 vòng sửa, liệt kê chi tiết:
```
ROW KHÔNG THỂ SỬA:
  Row {n} [{level}] {_id}:
    Lỗi: {mô tả lỗi cụ thể}
    Đã sửa: 3 vòng
    Gợi ý: {gợi ý xử lý thủ công}
```
