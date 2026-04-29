# Rules: Câu hỏi & Đáp án (R5, R6)

> **Scope**: Đoạn văn ngắn có **duy nhất 1 câu hỏi** per bài — các cột `question_2` → `question_5` LUÔN empty.

## R5. Câu hỏi đọc hiểu

### Nguyên tắc cốt lõi

- **100% căn cứ vào văn bản**: đáp án xác nhận rõ ràng bởi thông tin/ý trong bài. KHÔNG dựa kiến thức ngoài.
- **Không yêu cầu suy luận ngoài bài** — chỉ cần đọc đoạn văn là tìm được đáp án.
- **1 câu hỏi/bài** — đúng N1-N5. CSV column `question_1` duy nhất có value, `question_2` → `question_5` empty.
- **Không có ảnh trong câu hỏi** — `question_image_1` luôn empty.

### 7 kiểu câu hỏi (`question_label`)

Dùng `question_label_1` từ catalog — chọn theo intent câu hỏi:

| `question_label` | Khi nào dùng | Keywords câu hỏi |
|-------------------|--------------|-------------------|
| `question_content_match` | Chọn câu phù hợp với nội dung | 最も合っているもの, 正しいもの, 本文の内容と合うもの |
| `question_reason_explanation` | Hỏi lý do / nguyên nhân | なぜ, どうして, ～のはなぜか |
| `question_reference` | Hỏi đại từ chỉ định hoặc cụm được gạch chân | それ, これ, その, この, どんな〜か, 「...」とあるが |
| `question_meaning_interpretation` | Hỏi nghĩa của câu/cụm từ | どういうことか, どういう意味か |
| `question_content_mismatch` | Chọn câu KHÔNG phù hợp | 合わないもの, 正しくないもの, 間違っているもの |
| `question_author_opinion` | Hỏi quan điểm tác giả | 筆者の考え, 筆者は...と思っているか |
| `question_fill_in_the_blank` | Điền từ vào ô trống | [ ① ] に入る, ( 1 ) に入る最も適当なもの |

### Distribution đề xuất per level

Để batch đa dạng, phân bố theo level:

| Level | Nên dùng nhiều | Hạn chế dùng |
|-------|-----------------|--------------|
| **N5** | `content_match` (~70%), `reference` (~20%), `reason_explanation` (~10%) | `author_opinion`, `meaning_interpretation` (quá khó) |
| **N4** | `content_match` (~50%), `reference` (~20%), `reason_explanation` (~20%), `content_mismatch` (~10%) | `author_opinion` (quá khó) |
| **N3** | `reference` (~30%), `meaning_interpretation` (~25%), `content_match` (~20%), `reason_explanation` (~20%) | — |
| **N2** | `reason_explanation` (~25%), `reference` (~25%), `content_match` (~20%), `author_opinion` (~15%), `meaning_interpretation` (~15%) | — |
| **N1** | `fill_in_the_blank` (~25%), `author_opinion` (~25%), `meaning_interpretation` (~20%), `reason_explanation` (~20%), `reference` (~10%) | `content_mismatch` (quá đơn giản) |

> **BẮT BUỘC trong batch > 3 bài**: Không dùng cùng 1 `question_label` cho tất cả bài. Phân bổ ≥ 2 labels khác nhau (≥ 3 nếu batch > 5 bài).

### Câu hỏi pattern phổ biến theo level

**N1** — Formal, đòi hỏi suy luận:
- `筆者はどうして、…とのべているか。` — reason_explanation
- `引き出物の意味は何か` — meaning_interpretation
- `筆者がこの文書を書いた最もの目的はどれか。` — author_opinion
- `[ ① ] に入る最も適当なものはどれか` — fill_in_the_blank

**N2** — Cả reason + reference + content_match:
- `①しかたなしにやる、②…とあるが、〜` — reference (marker đa)
- `筆者は「情報化社会」をどのような社会と考えているか。` — author_opinion
- `①「いやだ」とあるが、なぜいやなのか。` — reason_explanation

**N3** — Reference + meaning_interpretation:
- `「『バ』まで言ってから気がついて」とあるが、どんなことに気がついたのか。` — reference
- `「ひとみしりをする質」とあるが、どんな性格か。` — meaning_interpretation

**N4** — Content match đơn giản:
- `どんな買い方がよくないと言っていますか。` — content_match
- `バナナはどのように食べたらおいしいと言っていますか` — content_match

**N5** — Very simple:
- `大川さんはあした何をするとかいてありますか。` — content_match (thư)
- `ただしい ものは どれですか。` — content_match

### Marker phải khớp với câu hỏi

Nếu câu hỏi thuộc `question_reference` hoặc `question_meaning_interpretation` → HTML bài đọc phải có marker tương ứng:

- `<u>cụm được hỏi</u>` — gạch chân cụm
- `<span class="marker">①</span>` — đánh số nếu có nhiều cụm
- `「cụm」とあるが、...` — câu hỏi nhắc lại cụm được gạch chân

**Cấm**: Đề có `<u>このような</u>` nhưng câu hỏi hỏi về cụm khác → REJECT.

Nếu câu hỏi thuộc `question_fill_in_the_blank` → HTML phải có blank marker (`[ ① ]`, `（ 1 ）`, hoặc `　ａ　`), và câu hỏi dùng đúng format đó.

### Paraphrasing — TẤT CẢ LEVEL

> **Áp dụng từ N5 đến N1. Không có ngoại lệ.**

Câu hỏi và đáp án đúng KHÔNG được copy nguyên văn từ bài → PHẢI dùng **từ đồng nghĩa hoặc cách diễn đạt tương đương**.

| Level | Mức paraphrase |
|-------|----------------|
| N5 | Đổi cấu trúc câu đơn giản, thay ≥1 từ chính bằng từ đồng nghĩa cùng level |
| N4 | Đổi cấu trúc câu + thay ≥2 từ/cụm từ |
| N3-N1 | Diễn đạt lại hoàn toàn, không trùng cụm ≥3 từ liên tiếp với bài gốc |

**Test paraphrase:** So đáp án đúng với bài gốc → nếu tìm thấy cụm ≥4 từ giống hệt = FAIL (N3+), ≥6 từ = FAIL (N4/N5).

Từ dùng để paraphrase phải đúng level thí sinh.

### Furigana trong câu hỏi

Cùng rule với bài đọc — chỉ cho từ vượt level. Câu hỏi thường dùng vocab level-appropriate, nên ít cần furigana.

### Nhất quán thì động từ

Câu hỏi + 4 lựa chọn phải **thống nhất thì** (ưu tiên thì hiện tại).

### Văn phong câu hỏi (thể động từ) theo level — BẮT BUỘC

Câu hỏi (`question_X`) và 4 lựa chọn (`answer_X`) phải dùng đúng **thể động từ** theo level:

| Level | Thể bắt buộc | Đặc trưng kết câu |
|-------|--------------|-------------------|
| **N1, N2, N3** | **Thể thường** (普通体 / だ・である調) | `〜か。` / `〜のはどれか。` / `〜と考えられるか。` (KHÔNG dùng です/ます) |
| **N4, N5** | **Thể ます** (です・ます調) | `〜ですか。` / `〜のはどれですか。` / `〜と思いますか。` |

**Quy tắc cứng:**
- N1/N2/N3: KHÔNG dùng `です` / `ます` trong câu hỏi và đáp án (trừ khi trích nguyên cảm trong bài)
- N4/N5: PHẢI dùng `です` / `ます` đầy đủ
- Câu hỏi và **cả 4 đáp án** phải nhất quán cùng thể (không trộn lẫn N3 thường + N4 ます)

---

## R6. Lựa chọn đáp án (Options)

### Nguyên tắc cốt lõi

- **Đáp án đúng**: xác nhận rõ bởi thông tin/ý trong bài, PHẢI paraphrase (mọi level).
- **Đáp án sai (distractor)**: PHẢI dùng **thông tin/concept THẬT từ bài** nhưng sai ngữ cảnh/hiểu lầm ý. **NGHIÊM CẤM bịa thông tin không có trong bài**.
- **Duy nhất 1 đáp án đúng tuyệt đối**.
- **Độ dài tương đương**: tỷ lệ dài/ngắn nhất < 2.0.
- **Từ vựng trong đáp án ≤ level thí sinh**.

### Answer format trong CSV

Mỗi `answer_1` chứa 4 options ngăn cách bởi `\n`, **KHÔNG có số thứ tự** trước mỗi đáp án:

```
Option A text\nOption B text\nOption C text\nOption D text
```

**⚠️ KHÔNG dùng** `1. `, `2. `, `3. `, `4. ` trước đáp án. Chỉ cần nội dung thuần.

`correct_answer_1` là số `1`, `2`, `3`, hoặc `4` (chỉ số thứ tự đáp án đúng, đếm từ 1).

**CHÚ Ý khi dùng data gốc**: JSON data gốc dùng `correctAnswer` index 0-based. Khi convert sang CSV, phải +1 → `correct_answer_1` = index + 1.

### ⛔ Phân bố vị trí đáp án đúng — KHÔNG lặp vị trí

> **Đáp án đúng PHẢI phân bố đều ở 4 vị trí (1, 2, 3, 4) trong batch.**
> KHÔNG được để tất cả đáp án đúng đều ở vị trí 1 — thí sinh sẽ nhận ra pattern.

Quy tắc:
- Trong batch (nhiều bài cùng level): phân bố đều 4 vị trí. Ví dụ 4 bài → đáp án đúng lần lượt ở vị trí 1, 3, 2, 4.
- **KHÔNG BAO GIỜ** có ≥3 bài liên tiếp cùng vị trí đáp án đúng.
- Agent phải **random vị trí** đáp án đúng trước khi sắp xếp 4 options, KHÔNG luôn đặt đáp án đúng ở vị trí 1 rồi shuffle sau.

### Distractor quality theo level

Mỗi distractor phải dùng concept hoặc chi tiết CÓ trong bài nhưng sai ở 1 điểm. Cụ thể:

| Level | Cách distractor sai |
|-------|----------------------|
| **N5** | Sai rõ ràng (thông tin ngược lại / không có trong bài) — thí sinh đọc lại bài là thấy sai |
| **N4** | Sai ở 1 chi tiết (thời gian, đối tượng, hành động) |
| **N3** | Sai ở 1 nuance (đảo ngược quan hệ, đảo ngược nhân-quả, hiểu nhầm chủ ngữ) |
| **N2** | Sai ở 1 giải thích (chọn lý do không chính xác, kết luận quá rộng/hẹp) |
| **N1** | Sai tinh vi — đúng 2/3 ý, sai 1 ý khó nhận ra. Cần đọc kỹ toàn bài. |

### ⛔ 4 loại bẫy — TẤT CẢ câu hỏi nên có ≥ 2 loại

| Loại bẫy | Mô tả | Tại sao khó loại |
|-----------|--------|-------------------|
| **① Bẫy đảo ngược (reversal)** | Đảo ngược quan hệ nhân-quả, chủ-vị, hoặc ý đối lập | Phải đọc kỹ câu quan trọng mới phát hiện |
| **② Bẫy chi tiết sai (detail swap)** | Dùng chi tiết THẬT từ bài nhưng gán cho đối tượng/thời điểm khác | Phải xác nhận đúng đối tượng/thời điểm mới loại |
| **③ Bẫy quá rộng/hẹp (scope)** | Kết luận quá chung hoặc quá cụ thể so với bài | Phải đánh giá chính xác scope của lập luận |
| **④ Bẫy hiểu nhầm ý (misinterpretation)** | Hiểu ý phụ thay vì ý chính, hoặc đảo ngược tone (tích cực ↔ tiêu cực) | Phải nắm đúng ý chính của bài |

### ⛔ Self-test BẮT BUỘC cho mỗi distractor

> **Agent PHẢI thực hiện self-test này cho TỪNG đáp án sai. Không được bỏ qua.**

Với mỗi đáp án sai, agent phải:
1. **Trích dẫn chính xác** câu/vị trí trong bài dùng để bác bỏ đáp án này (copy nguyên văn + ghi vị trí: paragraph nào, câu nào)
2. **Giải thích** tại sao đáp án này sai dựa trên trích dẫn đó
3. **Xác nhận** thông tin/ý trong đáp án sai CÓ xuất hiện trong bài (không bịa)

**REJECT ngay nếu:**
- Không trích dẫn được câu cụ thể từ bài → đáp án đang bịa thông tin
- Phải dùng kiến thức ngoài bài để loại → đáp án không có căn cứ bác bỏ trong bài

**Ví dụ SAI:**
> Bài nói: "バナナは熟してから食べた方がおいしい。"
> Đáp án sai: "バナナを冷蔵庫で冷やしてから食べるとおいしい。"
> → Bài KHÔNG nhắc tủ lạnh → BỊA → REJECT

**Ví dụ ĐÚNG:**
> Bài nói: "毎朝走っていたが、最近は雨が多くて外に出られない。"
> Câu hỏi: なぜ最近走っていないか。
> Đáp án đúng: 天気が悪いから。
> Đáp án sai (detail swap): 忙しくなったから。
> → Bài KHÔNG nói "忙しい" nhưng đáp án này dùng lý do hợp lý chung → REJECT nếu không xuất hiện trong bài
>
> Đáp án sai hợp lệ (reversal): 体調が悪いから。 → câu hỏi đã có thông tin "雨が多くて外に出られない" → bác bỏ rõ ràng

### Loại trừ tuyệt đối — REJECT nếu có bất kỳ

- Bịa thông tin không có trong bài (kể cả bịa 1 chi tiết nhỏ)
- Đáp án chỉ loại được bằng common sense, không cần đọc bài
- Sai hiển nhiên (loại ngay không cần đọc bài)
- 3 đáp án tích cực + 1 phủ định rõ ràng (pattern dễ đoán)
- Đáp án chỉ khác nhau 1 con số tròn (không áp dụng trong đoạn văn ngắn vì thường không có số liệu)
- Đáp án dùng từ vựng vượt level thí sinh
- **Test che bài**: che bài, nhìn 4 đáp án → đoán được = REJECT
- **Test loại nhanh**: đọc 1 đáp án sai, loại được trong <3 giây không cần quay lại bài = REJECT

### Format explanation — 3 phần BẮT BUỘC

> **Explanation không chỉ "có nội dung" — nó phải CHỨNG MINH câu hỏi + đáp án đúng logic.**
> Agent viết `explain_vn_1` và `explain_en_1` theo đúng 3 phần sau.

**Phần 1 — Đáp án đúng:** Giải thích TẠI SAO đáp án đúng là đúng. Trích dẫn cụ thể vị trí/câu trong bài (ví dụ: "Trong đoạn 2, tác giả viết rằng...", "Câu cuối nói..."). Cross-reference ý trong bài.

**Phần 2 — Đáp án sai:** Giải thích TẠI SAO từng đáp án sai là sai. Nêu rõ loại bẫy (reversal / detail swap / scope / misinterpretation) và chỉ ra thông tin/ý nào trong bài khiến đáp án đó sai.

**Phần 3 — Tóm tắt:** 1 câu ngắn tóm lại logic tìm đáp án.

**Ví dụ `explain_vn_1` (bài N3 về "禁止令"):**
```
ĐÁP ÁN ĐÚNG (2): 子供に「バ」と言いかけて途中でやめたこと。
Theo đoạn 2, tác giả viết "「バ」まで言ってから気がついて、子供はその後「……ビブベボ」".
Rõ ràng đứa trẻ đã nói chữ "バ" rồi mới dừng lại và chữa thành "ビブベボ".

ĐÁP ÁN SAI:
(1) バカと言ってしまったこと — detail swap: Bài nói rõ là DỪNG lại ở "バ", chưa nói hết "バカ".
(3) 家族で大笑いしたこと — misinterpretation: Đây là kết quả, không phải điều đứa trẻ phát hiện.
(4) 言葉を選ぶ難しさに気づいたこと — scope: Đây là ý của tác giả ở cuối bài, không phải điều trẻ phát hiện.

Tóm tắt: Cần đọc kỹ đoạn 2 để hiểu trẻ đã dừng lại đúng lúc và tự sửa lời.
```

**Explanation phải bằng cả 2 ngôn ngữ (VN + EN)** với cùng nội dung logic.
