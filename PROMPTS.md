# PROMPTS.md — Đoạn Văn Ngắn

Prompt templates cho skill `jlpt-reading-short-passage`. Thiết kế cho việc gen batch đa level.

## Cách dùng

User chỉ cần nói: **"Gen 3 bài mỗi level"** → AI agent tự hiểu = 3 × 5 levels = 15 bài tổng.

Hoặc cụ thể hơn: **"Gen 5 bài N3"** → 5 bài chỉ N3.

---

## 1. Prompt chính — Gen batch đa level

Đây là prompt duy nhất cần dùng cho hầu hết mọi trường hợp.

```
Gen {N} bài JLPT đoạn văn ngắn cho MỖI level (N1, N2, N3, N4, N5).
Tổng cộng: {N} × 5 = {TOTAL} bài.

QUY TẮC BẮT BUỘC:

1. WORKFLOW — Cho MỖI BÀI (lặp {TOTAL} lần):
   a. Gen HTML theo template chuẩn (xem SKILL.md)
   b. Đếm ký tự — phải nằm trong Target Range, dưới Hard Reject → gen lại
   c. Save HTML vào assets/html/doan_van_ngan/{LEVEL}_{uuid}.html
   d. Chạy process_html.py để append vào CSV NGAY LẬP TỨC
   e. KHÔNG gen hết rồi mới save — save từng bài một

2. ĐA DẠNG trong mỗi level:
   - Topic (tag): không trùng nhau trong cùng level, chọn từ ≥ 3 nhóm khác nhau
     (Đời sống, Xã hội, Công việc, Giáo dục, Kinh tế, Khoa học, Văn học)
   - question_label: dùng ≥ 2 labels khác nhau per level (nếu N ≥ 2)

3. ĐỘ DÀI (Target Range — đếm không whitespace, không <rt>):
   - N1: 220–260 chars | Hard Reject < 200
   - N2: 240–290 chars | Hard Reject < 200
   - N3: 220–290 chars | Hard Reject < 200
   - N4: 180–240 chars | Hard Reject < 150
   - N5: 100–160 chars | Hard Reject < 80

4. FURIGANA: chỉ cho từ VƯỢT level. Cấm dạng "Ab" (nửa kanji nửa hiragana).
   Ưu tiên thay bằng từ đơn giản hơn thay vì rắc furigana.

5. ANNOTATION (注): giải thích bằng TIẾNG NHẬT ĐƠN GIẢN (やさしい日本語).
   Bài đọc JLPT phải full tiếng Nhật — KHÔNG dùng tiếng Anh hay tiếng Việt.
   Ví dụ: 注1 禁止令：してはいけないという決まり ✅ | 注1 禁止令：prohibition order ❌
   Chỉ thêm cho N1/N2/N3 khi có thuật ngữ chuyên ngành. N4/N5 KHÔNG có annotation.

6. ĐÁP ÁN: 4 options ngăn cách bởi \n, KHÔNG có số thứ tự.
   ✅ "選択肢A\n選択肢B\n選択肢C\n選択肢D"
   ❌ "1. 選択肢A\n2. 選択肢B\n3. 選択肢C\n4. 選択肢D"

7. SOURCE LINE: chỉ N1/N2/N3, tên tác giả TỰ CHẾ (không dùng tên thật).

8. CSV: sau khi gen xong TẤT CẢ {TOTAL} bài, file CSV PHẢI có đúng {TOTAL} rows mới.
   Verify bằng: python3 process_html.py --validate --html-dir assets/html/doan_van_ngan

QUY CÁCH PER LEVEL:

【N1】 Formal essay/phê bình
- Văn phong: rất formal, keigo, ～いかんによらず, ～をもって, ～に先立ち
- 1–2 paragraph | 0–1 ruby | annotation optional | source optional
- question_label phổ biến: fill_in_the_blank (~25%), author_opinion (~25%),
  meaning_interpretation (~20%), reason_explanation (~20%)

【N2】 Tiểu luận, marker phổ biến
- Văn phong: formal văn viết, ～に伴い, ～に基づき, ～を踏まえて
- 2–3 paragraph | 0–2 ruby | annotation optional | source optional
- question_label phổ biến: reason_explanation, reference, content_match,
  author_opinion, meaning_interpretation (đa dạng)

【N3】 Giai thoại/tư vấn, annotation nhiều
- Văn phong: nửa formal nửa conversational, ～について, ～によって, ～ために
- 2–3 paragraph | 0–3 ruby | annotation KHUYẾN KHÍCH | source optional
- question_label phổ biến: reference (~30%), meaning_interpretation (~25%),
  content_match (~20%), reason_explanation (~20%)

【N4】 Đời sống đơn giản
- Văn phong: lịch sự đơn giản, ～ことができます, ～と思います
- 2–3 paragraph, câu ngắn | 0–2 ruby | KHÔNG annotation | KHÔNG source
- question_label phổ biến: content_match (~50%), reference (~20%),
  reason_explanation (~20%), content_mismatch (~10%)

【N5】 Thư/lời nhắn đơn giản
- Văn phong: thân mật, hiragana nhiều, ～です/～ます, full-width space giữa cụm từ
- 1 paragraph (hoặc letter format với <br>) | 0–1 ruby | KHÔNG annotation | KHÔNG source
- question_label phổ biến: content_match (~70%), reference (~20%),
  reason_explanation (~10%)

OUTPUT cho mỗi bài: JSON object
{
  "id": "{LEVEL}_{uuid32hex}",
  "level": "{LEVEL}",
  "tag": "{topic tiếng Việt}",
  "html": "<!DOCTYPE html>...",
  "question_label": "question_content_match",
  "question": "câu hỏi tiếng Nhật",
  "answers": ["đáp án A", "đáp án B", "đáp án C", "đáp án D"],
  "correct_answer": 2,
  "explain_vn": "Giải thích tiếng Việt...",
  "explain_en": "English explanation..."
}
```

---

## 2. Prompt gen 1 level cụ thể

Khi chỉ cần gen cho 1 level:

```
Gen {N} bài JLPT {LEVEL} đoạn văn ngắn.

Tuân thủ tất cả quy tắc trong SKILL.md. Đặc biệt:
- Target Range: {LO}–{HI} chars
- Topic đa dạng: ≥ {min(N, 3)} topics khác nhau
- question_label đa dạng: ≥ {min(N, 3)} labels khác nhau
- Annotation bằng TIẾNG VIỆT (không Anh)
- Đáp án KHÔNG có số thứ tự
- Save HTML + CSV TỪNG BÀI MỘT

Output: array of {N} JSON objects.
```

---

## 3. Prompt fix bài fail

### Bài dưới Target Range (nhưng trên Hard Reject)

```
Bài {ID} có {CHARS} ký tự, dưới Target Range ({LO}-{HI}).

Bổ sung thêm nội dung bằng 1 trong các cách (theo ưu tiên):
1. Thêm 1 câu văn vào paragraph cuối (mở rộng ý, không ý mới)
2. Thêm chú thích 注 bằng tiếng Việt (nếu N1-N3)
3. Mở rộng description 1 đáp án

Giữ nguyên: _id, question_label, câu hỏi, đáp án đúng.
Output: JSON object mới.
```

### Bài dưới Hard Reject → gen lại hoàn toàn

```
Bài {ID} có {CHARS} ký tự, DƯỚI Hard Reject ({THRESHOLD}).
GEN LẠI TỪ ĐẦU. Cùng level {LEVEL}, target {LO}-{HI}.
Topic: {TOPIC}. question_label: {LABEL}.
Output: JSON object mới.
```

### Bài có annotation tiếng Anh/Việt → sửa sang tiếng Nhật

```
Bài {ID} có annotation không phải tiếng Nhật: "{WRONG_TEXT}".
Sửa lại thành tiếng Nhật đơn giản (やさしい日本語). Giữ nguyên tất cả phần khác.
Output: JSON object mới (chỉ HTML thay đổi).
```

### Bài có đáp án có số thứ tự → sửa

```
Bài {ID} có answer format sai: "1. X\n2. Y\n3. Z\n4. W".
Sửa lại thành: "X\nY\nZ\nW" (bỏ số thứ tự).
Giữ nguyên correct_answer và tất cả phần khác.
```

---

## 4. Prompt verify batch

```
Kiểm tra chất lượng {TOTAL} bài JLPT đoạn văn ngắn (N1-N5, {N} bài/level).

Cho mỗi bài, đánh giá:
1. Độ dài trong Target Range:           PASS / FAIL
2. Furigana đúng quy tắc:               PASS / FAIL
3. Annotation bằng tiếng Nhật đơn giản:  PASS / FAIL
4. Đáp án không có số thứ tự:           PASS / FAIL
5. Chỉ 1 đáp án đúng:                   PASS / FAIL
6. Distractor plausible:                 PASS / FAIL
7. Câu hỏi answer được từ trong bài:    PASS / FAIL
8. Giải thích VN + EN non-empty:        PASS / FAIL

Batch-level:
- Mỗi level có ≥ 2 question_label khác nhau?  YES / NO
- Mỗi level có ≥ 2 tag khác nhau?              YES / NO
- Tất cả _id unique?                           YES / NO
- Tổng rows trong CSV = {TOTAL}?               YES / NO

Output: bảng markdown + summary.
```

---

## 5. Ví dụ sử dụng thực tế

| User nói | AI hiểu | Tổng bài |
|----------|---------|----------|
| "Gen 3 bài mỗi level" | 3 × 5 levels | **15 bài** |
| "Gen 5 bài N3" | 5 bài chỉ N3 | **5 bài** |
| "Gen 2 bài N1 và 3 bài N5" | 2 N1 + 3 N5 | **5 bài** |
| "Gen 10 bài mỗi level" | 10 × 5 levels | **50 bài** |
| "Gen 1 bài thử N4" | 1 bài N4 | **1 bài** |

---

## 6. Checklist nhanh trước khi gen

Trước khi bắt đầu gen batch, AI agent cần:

- [ ] Đọc SKILL.md để nắm đầy đủ quy tắc
- [ ] Đọc references/html-patterns.md để biết template per level
- [ ] Load 1-2 sample per level bằng `load_references.py --level {LEVEL} --count 2`
- [ ] Chuẩn bị danh sách topic + question_label phân bổ đa dạng cho batch
- [ ] Xác nhận thư mục output: `assets/html/doan_van_ngan/` và `sheets/samples_v1.csv`
