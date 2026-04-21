# Sample Analysis — Đoạn Văn Ngắn Reference Data

Phân tích định lượng dữ liệu mẫu thực tế ở `data/doan_van_ngan_n{1-5}_clean.json` để gen agent biết **chính xác** mức độ dài, cấu trúc câu hỏi, và pattern HTML nào phổ biến ở mỗi level.

Số liệu chạy bằng `load_references.py --stats` + phân tích pattern.

## 1. Phân Bố Độ Dài (`jp_char_count`)

| Level | Samples | Min | P25 | P50 (median) | P75 | Avg | Max |
|-------|---------|-----|-----|--------------|-----|-----|-----|
| N1    | 104     | 201 | 220 | 236          | 252 | 240 | 447 |
| N2    | 205     | 202 | 238 | 258          | 291 | 273 | 645 |
| N3    | 140     | 200 | 216 | 236          | 287 | 255 | 497 |
| N4    | 124     | 151 | 181 | 202          | 234 | 216 | 438 |
| N5    | 105     | 80  | 97  | 111          | 151 | 130 | 298 |

**Kết luận**:
- **Target range** khuyến nghị = P25–P75 (giữ bài giữa mainstream, không quá dài/ngắn)
- **Hard reject** = dưới Min thực tế → bài quá ngắn, JLPT không chấp nhận
- Dài hơn Max thực tế một chút thì OK, nhưng đa số outliers trên P75 thường là bài có annotation dài → nên tự hỏi "có cần thiết dài vậy không?"

## 2. Số Câu Hỏi Per Sample

| Level | 1 question | 2 questions | 3+ |
|-------|-----------|-------------|-----|
| N1    | 104 (100%) | 0          | 0 |
| N2    | 194 (95%)  | 11 (5%)    | 0 |
| N3    | 137 (98%)  | 3 (2%)     | 0 |
| N4    | 123 (99%)  | 1 (1%)     | 0 |
| N5    | 105 (100%) | 0          | 0 |

**Kết luận**: Đoạn văn ngắn chuẩn JLPT là **1 câu/bài**. Một vài sample N2/N3 có 2 câu nhưng đó là ngoại lệ (thường do bài có 2 marker ①② cần hỏi cả hai). Trong skill này **luôn gen 1 câu/bài** để đơn giản, các column `question_2`..`question_5` luôn empty.

## 3. Pattern HTML Phổ Biến

### Pattern thô trong data gốc

| Pattern                | N1       | N2       | N3       | N4       | N5       |
|------------------------|----------|----------|----------|----------|----------|
| Có `<p>`               | 97%      | 82%      | 70%      | 95%      | 85%      |
| Có `<br>`              | 36%      | 44%      | 38%      | 4%       | 15%      |
| Có `<ruby>`            | 0%       | 5%       | 7%       | 12%      | 8%       |
| Có `<span>`            | 0%       | 18%      | 19%      | 18%      | 9%       |
| Có `<u>` (underline)   | 1%       | 0%       | 5%       | 2%       | 2%       |
| Có 注 annotation       | 19%      | 28%      | 40%      | 12%      | 0%       |
| Có source line         | 5%       | 6%       | 7%       | 0%       | 0%       |
| Có marker ①②③④         | 3%       | 7%       | 4%       | 0%       | 0%       |
| Có blank [ ① ]/(1)     | 26%      | 1%       | 2%       | 5%       | 3%       |

### Nhận xét & Rule cho Output Skill

1. **`<br>` rải rác ở N1/N2/N3 (36–44%)**: Đây là **thói quen xấu** từ data gốc (xuống hàng thủ công để rộng ra giấy). Output của skill **KHÔNG dùng `<br>` giữa câu** — dùng `<p>` thuần, text flow liên tục. Ngoại lệ duy nhất là N5 format thư.

2. **`<ruby>` thấp ở N1/N2 (0-5%)**: Do bài N1/N2 dùng toàn kanji đúng level nên không cần furigana. **Skill áp dụng đúng**: ruby chỉ cho từ vượt level.

3. **`<ruby>` cao ở N4 (12%)**: Data N4 có thói quen rắc ruby trên từ đúng level (`本当`, `場所`, `捨てる`). **Skill KHÔNG theo pattern này** — chỉ furigana cho từ trên N4.

4. **`<span>` dùng để bọc paragraph ở N2-N5 (9–19%)**: Không có lý do semantic. **Skill không cần `<span>`** trừ khi thật sự cần styling inline.

5. **注 annotation (N3 cao nhất 40%)**: Đây là pattern chuẩn JLPT. Skill **nên khuyến khích thêm 注** ở N1/N2/N3 khi bài có thuật ngữ chuyên ngành. N4 có ít hơn (12%), N5 không có.

6. **Source line (`（...による）`) chỉ ở N1-N3 (5-7%)**: Pattern formal cho bài essay/phê bình. Skill có thể thêm cho N1/N2/N3 khi bài là essay/commentary. **KHÔNG thêm cho N4/N5.**

7. **Marker ①②③④ (N2 cao nhất 7%)**: Dùng cho bài có câu hỏi reference hoặc bài phân tích nhiều đoạn. Skill dùng marker khi `question_label` = `question_reference` hoặc `question_meaning_interpretation`.

8. **Blank fill [ ① ] (N1 cao nhất 26%)**: Pattern điển hình của question_fill_in_the_blank. **Chú ý N1 có tới 26% bài fill-in-blank** — distribution câu hỏi của skill N1 nên phản ánh điều này.

## 4. Câu Hỏi Phổ Biến Theo Level

### N1 — Formal, đòi hỏi suy luận

- `筆者はどうして、…とのべているか。` — reason_explanation
- `引き出物の意味は何か` — meaning_interpretation
- `筆者がこの文書を書いた最もの目的はどれか。` — author_opinion
- `[ ① ] に入る最も適当なものはどれか` — fill_in_the_blank (khá phổ biến ở N1)

### N2 — Cả reason + reference + content_match

- `①しかたなしにやる、②…、③…、④…とあるが、〜` — reference (đa marker)
- `筆者は「情報化社会」をどのような社会と考えているか。` — author_opinion
- `①「いやだ」とあるが、なぜいやなのか。` — reason_explanation

### N3 — Reference + meaning_interpretation

- `「『バ』まで言ってから気がついて」とあるが、どんなことに気がついたのか。` — reference
- `「ひとみしりをする質」とあるが、どんな性格か。` — meaning_interpretation
- `「この事情は、基本的には現在も変わっていない」とあるが、この事情とはどのようなことか。` — reference

### N4 — Content match đơn giản

- `どんな買い方がよくないと言っていますか。` — content_match
- `バナナはどのように食べたらおいしいと言っていますか` — content_match
- `この動物園はどう変わりましたか` — content_match

### N5 — Very simple

- `大川さんはあした何をするとかいてありますか。` — content_match (dựa trên thư)
- `ただしい ものは どれですか。` — content_match
- `あなたは この たてものの 中で 何を しますか。` — content_match

## 5. Distribution `question_label` Đề Xuất (dựa trên data + mission.json)

Dựa vào phân bố thực tế + độ phù hợp với level:

### N1 (104 samples)
- `fill_in_the_blank`: ~25%
- `author_opinion`: ~25%
- `meaning_interpretation`: ~20%
- `reason_explanation`: ~20%
- `reference`: ~10%

### N2 (205 samples)
- `reason_explanation`: ~25%
- `reference`: ~25% (marker ①②③④ đặc biệt phổ biến)
- `content_match`: ~20%
- `author_opinion`: ~15%
- `meaning_interpretation`: ~15%

### N3 (140 samples)
- `reference`: ~30%
- `meaning_interpretation`: ~25%
- `content_match`: ~20%
- `reason_explanation`: ~20%
- Khác: ~5%

### N4 (124 samples)
- `content_match`: ~50%
- `reference`: ~20%
- `reason_explanation`: ~20%
- `content_mismatch`: ~10%

### N5 (105 samples)
- `content_match`: ~70%
- `reference`: ~20%
- `reason_explanation`: ~10%

## 6. Chủ Đề Phổ Biến (heuristic từ đọc sample)

| Level | Chủ đề hay gặp |
|-------|----------------|
| N1    | Triết học văn hóa (俳句, 遺産, 芸術), phê bình xã hội, email công việc formal |
| N2    | Tiểu luận về đời sống (gia đình, công việc), phê bình văn hóa, bài báo nhẹ |
| N3    | Giai thoại gia đình (子育て, しつけ), bài báo ngắn về xã hội, tư vấn |
| N4    | Lời khuyên tiêu dùng, thông báo lớp học, hội thoại ngắn, động vật học |
| N5    | Thư/lời nhắn (メモ, 手紙), nhật ký 1 ngày, thông báo đơn giản |

## 7. Rule Tóm Lược Cho Gen Agent

1. **Độ dài**: Luôn rơi vào P25–P75 target, không dưới Min của level
2. **Cấu trúc HTML**: `<p>` + text-indent 1em, KHÔNG `<br>` giữa câu (trừ N5 letter)
3. **Furigana**: Chỉ cho từ vượt level, tuyệt đối không rắc đều như data gốc
4. **注 annotation**: Thêm ở N1/N2/N3 khi có thuật ngữ; không thêm cho N4/N5
5. **Source line**: Thêm `（[fake author]「[fake title]」による）` khi bài là essay/phê bình (N1-N3); không thêm N4/N5
6. **Marker ①②③④**: Dùng khi `question_label` là reference/meaning_interpretation
7. **Blank `[ ① ]`**: Dùng khi `question_label` là fill_in_the_blank
8. **1 câu hỏi/bài** — luôn luôn. `question_2`..`question_5` = empty
9. **question_label distribution** trong batch ≥ 5 bài: ≥ 3 labels khác nhau
