# Rules: Nội dung, Layout, Format & Visual (R1, R2, R7, R8)

> **Scope**: Đoạn văn ngắn (短文 / short-passage) — văn xuôi Nhật 80-290 ký tự với **1 câu hỏi** trắc nghiệm.

## R1. Chủ đề & Văn phong theo level

> **NGUYÊN TẮC**: Đoạn văn ngắn là văn xuôi (prose) — test khả năng **hiểu nội dung / nắm ý chính / suy luận quan hệ nhân-quả / hiểu ý tác giả**. Không phải tra cứu bảng giá/lịch, không phải đọc sơ đồ.

| Level | Chủ đề | Văn phong | Cấu trúc câu |
|-------|--------|-----------|--------------|
| **N5** | Thư/lời nhắn (メモ, 手紙), nhật ký 1 ngày, thông báo đơn giản | Thân mật, nhiều hiragana, có full-width space `　` giữa cụm từ | ～です/～ます, ～てください |
| **N4** | Lời khuyên tiêu dùng, mô tả đời sống, thời tiết, lịch học, hội thoại ngắn | Lịch sự đơn giản | ～ことができます, ～なければなりません, ～と思います |
| **N3** | Giai thoại gia đình (子育て, しつけ), bài báo ngắn, tư vấn, thư người lớn | Nửa formal nửa conversational | ～について, ～によって, ～場合は, ～ために |
| **N2** | Tiểu luận về đời sống, phê bình văn hóa nhẹ, email công việc, giai thoại | Formal, văn viết | ～に伴い, ～に基づき, ～を踏まえて, ～に限り |
| **N1** | Luận điểm triết học/văn hóa cô đọng (俳句, 遺産, 芸術), phê bình xã hội, email formal | Rất formal, văn viết cao cấp | ～いかんによらず, ～をもって, ～に先立ち, keigo |

### Topic tag (tiếng Anh) — BẮT BUỘC

Tag PHẢI bằng **tiếng Anh**. Catalog category dưới đây (tham khảo `rules/rule_doc_hieu.md` từ giáo viên cho tinh thần ra đề):

| Category | Ví dụ tag |
|----------|----------|
| Personal Life & Psychology | `psychology`, `emotion`, `mindset`, `motivation`, `personal growth`, `happiness`, `childhood` |
| Society & Relationships | `society`, `family`, `relationships`, `friendship`, `parenting`, `tradition`, `etiquette` |
| Education & Language | `education`, `school`, `learning`, `language`, `communication`, `library` |
| Business, Economics & Finance | `economics`, `business`, `market`, `consumption`, `personal finance` |
| Work & Career | `work`, `career`, `workplace`, `announcement`, `correspondence` |
| Science & Technology | `science`, `biology`, `technology`, `research`, `energy` |
| Health & Medicine | `health`, `medicine`, `nutrition`, `diet`, `exercise`, `stress` |
| Environment & Nature | `environment`, `nature`, `animals`, `weather`, `season`, `recycling` |
| Culture, Arts & Entertainment | `culture`, `art`, `music`, `literature`, `philosophy`, `sports`, `travel` |
| Daily Life & Consumerism | `daily life`, `shopping`, `food`, `cooking`, `restaurant`, `pets` |
| Infrastructure & Media | `transportation`, `city`, `media`, `journalism` |

> **⚠️ KHÔNG dùng tag tiếng Việt** (ví dụ: ❌ `nhật ký`, `kinh tế`, `văn hóa`).
> Phải dùng tiếng Anh slug (ví dụ: ✅ `daily life`, `economics`, `culture`).

Trong batch > 5 bài, chọn topic từ ≥ 3 category khác nhau để đa dạng.

---

## R2. Format văn bản & Độ dài

### Target character count (BẮT BUỘC tuân thủ)

Đo bằng `count_body_chars()` — đếm **ký tự visible trong body**, bỏ whitespace, bỏ `<rt>` furigana.

| Level | Target Range (P25–P75) | Hard Reject (< Min) | Min Sample Data | Max Sample Data |
|-------|------------------------|---------------------|-----------------|-----------------|
| N1    | **220–260**            | < 200 → gen lại     | 201             | 447             |
| N2    | **240–290**            | < 200 → gen lại     | 202             | 645             |
| N3    | **220–290**            | < 200 → gen lại     | 200             | 497             |
| N4    | **180–240**            | < 150 → gen lại     | 151             | 438             |
| N5    | **100–160**            | < 80 → gen lại      | 80              | 298             |

> **🚫 HARD REJECT**: Nếu `count_body_chars()` **thấp hơn Hard Reject threshold**, bài **PHẢI gen lại từ đầu**. Không chấp nhận, không chỉnh sửa nhỏ — gen lại hoàn toàn.
> **⚠️ UNDER TARGET**: Dưới Target Range nhưng ≥ Hard Reject → bổ sung 1 câu văn ngắn hoặc thêm 1 chú thích `注`. Không tự thêm whitespace.
> **⚠️ OVER TARGET**: Cho phép dài hơn hi +30 chars; quá nhiều thì cảnh báo.

### Flow text (KHÔNG `<br>` giữa câu)

> **⛔ LỖI PHỔ BIẾN**: Data gốc dùng `<br>` thay `<p>` (thói quen xấu từ người soạn đề).
> **Output của skill KHÔNG dùng `<br>` giữa câu** — dùng `<p>` thuần, text flow liên tục.

**Quy tắc:**
- **ĐÚNG**: `<p>Câu 1。Câu 2。Câu 3。</p>` — 1 paragraph 1 `<p>`, câu nằm liền mạch.
- **SAI → REJECT**: `<p>Câu 1。<br>Câu 2。<br>Câu 3。</p>` — có `。<br>`.
- **Ngắt paragraph** chỉ khi chuyển ý hoàn toàn khác.
- **Xuống hàng trong source code** (edit view) chỉ để dễ đọc khi chỉnh sửa — HTML parser sẽ collapse whitespace.

**Ngoại lệ duy nhất — N5 letter format**:

```html
<!-- ✅ OK cho N5 vì letter cần giữ format xuống hàng -->
<p class="no-indent">「ヤンさんへ<br>
きょうは　先に　かえります。<br>
ヤンさんに　かりた　ノートは　あした　もって　きます。<br>
　　　大川　ひろし」</p>
```

### CSS layout bắt buộc

- **Container**: `max-width: 640px`, `margin: 0 auto`, white background trên light gray body
- **Body**: `word-break: keep-all`, `line-break: strict`, `overflow-wrap: break-word`
  (`keep-all` đảm bảo xuống dòng ở ranh giới từ, tránh cắt kanji compound giữa chừng)
- **Paragraph**: `<p>` với `text-indent: 1em` (chuẩn văn Nhật)
- **Font**: Noto Sans JP qua Google Fonts (KHÔNG dùng Tailwind CDN)
- **N5 đặc biệt**: thêm full-width space `　` giữa các cụm từ (mô phỏng đề N5 thật vì N5 chưa phân biệt rõ từ)

Template chi tiết xem `rules/technical.md` R9.

### Test mơ hồ (BẮT BUỘC)

> **Mỗi đoạn văn phải có DUY NHẤT 1 cách hiểu hợp lý.**
> Sau khi viết xong, đọc lại từng câu: "Câu này có hiểu theo cách thứ 2 không?" Nếu có → sửa lại cho rõ ràng.

---

## R7. Các dạng bài (document formats)

Đoạn văn ngắn có 6 dạng chính dưới đây — mỗi bài chọn đúng 1 dạng. Trong batch > 5 bài, nên xoay vòng ít nhất 3 dạng khác nhau.

| # | Format | Level | Đặc điểm | Ví dụ chủ đề |
|---|--------|-------|----------|--------------|
| 1 | **Essay/commentary** | N1, N2, N3 | 2-3 paragraph văn nghị luận, có thể có source line | 俳句, 遺産, 芸術, 言葉 |
| 2 | **Anecdote/story** | N2, N3 | Giai thoại đời thường, có thể có marker ①② | 子育て, 家族, しつけ |
| 3 | **Advice/tip** | N3, N4 | Lời khuyên tiêu dùng/đời sống | 買い物, 食事, 健康 |
| 4 | **News brief** | N2, N3 | Bài báo ngắn, không source line | 社会, 文化, 動物 |
| 5 | **Letter/message** | N5 | Thư ngắn, メモ, lời nhắn — cho phép `<br>` | 友だちへ, お知らせ |
| 6 | **Diary/note** | N4, N5 | Nhật ký 1 ngày, ghi chú đơn giản | 今日, 昨日, 予定 |

**Phân bố tần suất theo level (scan `data/` để chọn format chưa/ít dùng trong batch):**

- N1: 100% essay/commentary
- N2: ~60% essay, ~30% anecdote, ~10% news brief
- N3: ~40% anecdote, ~30% essay, ~20% advice, ~10% news brief
- N4: ~50% advice, ~30% diary, ~20% news brief
- N5: ~60% letter/message, ~40% diary

### Source line (`（author「title」による）`)

Tần suất thực tế trong data:

| Level | Tần suất | Nên dùng khi |
|-------|----------|--------------|
| N1    | 7%       | Bài essay/phê bình |
| N2    | 7%       | Bài tiểu luận/báo |
| N3    | 8%       | Thỉnh thoảng — essay nghiêm túc |
| N4    | 0%       | **KHÔNG** |
| N5    | 0%       | **KHÔNG** |

**Format**: `（[fake_author]「[fake_title]」[media?]による）`
- **Author**: tên Nhật 2-4 chữ, **tự chế** (không dùng tên tác giả có thật)
- **Title**: title tự chế phù hợp chủ đề
- **Media** (optional): `新聞`, `雑誌`, `文春社`, hoặc bỏ qua
- **⛔ Cấm**: dùng tên tác giả có thật (村上春樹, 夏目漱石, ...) — chạm IP

**Fake author pool:**
```
山田太郎, 佐藤花子, 鈴木一郎, 田中美和子, 高橋健太, 伊藤由美,
中村明, 小林さとし, 加藤けいこ, 吉田あきら, 山口まり, 斎藤ひろし
```

**Ví dụ:**
- `（山田太郎「日本語の楽しみ」朝日新聞による）`
- `（佐藤花子「暮らしの言葉」文春社による）`
- `（鈴木一郎「現代社会論」による）`

---

## R8. Visual elements (marker, annotation, blank)

### Marker cho Reference/Meaning Question

Dùng `<u>` để gạch chân cụm từ được hỏi, kết hợp `<span class="marker">①</span>` nếu có nhiều cụm.

**Single underline (1 cụm)**:
```html
<p>...と、<u>このような考え方</u>が広がっている。</p>
```
→ Câu hỏi: `「このような考え方」とあるが、どのような考え方か。`

**Multiple markers (2+ cụm — N2/N1)**:
```html
<p><span class="marker">①</span><u>古典的な勘違い</u>と、<span class="marker">②</span><u>仕方なしにやる</u>行為</p>
```
→ Câu hỏi: `①「古典的な勘違い」、②「仕方なしにやる」とあるが、〜`

### Marker cho Fill-in-Blank

3 style, chọn 1 theo level:

| Style | Level | Text trong HTML | Câu hỏi |
|-------|-------|-----------------|---------|
| `[ ① ]` | N1, N2 | `彼は[ ① ]と言った` | `[ ① ] に入る最も適当なものはどれか` |
| `（ 1 ）` | N2, N3 | `これは（ 1 ）問題だ` | `（ 1 ） に入る最も適当なものはどれか` |
| `　ａ　` | N3, N4 | `この花は　ａ　きれいだ` | `ａに入る最も適当なものはどれか` |

Quy ước:
- N1 hay dùng `[ ① ]` (fancy hơn)
- N3 hay dùng `（ 1 ）` hoặc `ａ`
- Luôn có khoảng trắng xung quanh để đọc dễ

### 注 Annotation

Block annotation ở cuối bài, style dashed border ngăn cách:

```html
<div class="annotations">
    <p>注1 〜〜〜：〜〜〜</p>
    <p>注2 〜〜〜：〜〜〜</p>
</div>
```

**Rules**:
- Đánh số `注1`, `注2`, `注3` tuần tự trong cùng bài
- Format: `注{N} {term}：{やさしい日本語で説明}` — `：` (full-width colon)
- Term là tiếng Nhật (kanji/từ khó)
- Định nghĩa **bằng tiếng Nhật đơn giản hơn** (やさしい日本語). **KHÔNG dùng tiếng Anh hay tiếng Việt** — bài đọc JLPT phải full tiếng Nhật.

**Tần suất theo level:**

| Level | Tần suất data | Nên dùng khi |
|-------|---------------|--------------|
| N1    | 19%           | Bài có thuật ngữ triết học/chuyên ngành |
| N2    | 28%           | Bài có keyword văn hóa/xã hội |
| N3    | 40%           | Bài có từ loại N2+ không thay được (pattern chuẩn JLPT) |
| N4    | 12%           | Ít khi — chỉ khi có từ không thể tránh |
| N5    | 0%            | **KHÔNG bao giờ** |

**Examples:**
```
注1 芸術：人間がつくりだす美しいもの
注1 信仰：強く信じること
注2 禁止令：してはいけないという決まり
注1 生成可能体：新しくつくり出せるもの
注1 伝統的遺産：昔から伝わる大切なもの
```

### Visual elements cheatsheet

| Element | HTML | Khi nào dùng |
|---------|------|--------------|
| Gạch chân | `<u>…</u>` | Cụm từ được hỏi (reference/meaning) |
| Marker số | `<span class="marker">①</span>` | Bài có 2+ cụm reference |
| Furigana | `<ruby>漢字<rt>かんじ</rt></ruby>` | Chỉ cho từ vượt level (xem R4) |
| Blank | `[ ① ]`, `（ 1 ）`, `　ａ　` | fill_in_the_blank |
| Chú thích | `<div class="annotations">` | N1/N2/N3 với thuật ngữ |
| Source | `<p class="source">` | N1/N2/N3 bài essay/phê bình |
| Full-width space | `　` | N5 giữa cụm từ (để dễ đọc) |

### "Should I include X?" theo level

| Feature | N1 | N2 | N3 | N4 | N5 |
|---------|-----|-----|-----|-----|-----|
| `<p>` wrapper | ✅ | ✅ | ✅ | ✅ | ✅ |
| `text-indent: 1em` | ✅ | ✅ | ✅ | ✅ | ✅ (trừ letter) |
| `<br>` giữa câu | ❌ | ❌ | ❌ | ❌ | ❌ (chỉ letter) |
| `<ruby>` | 0-1 | 0-2 | 0-3 | 0-2 | 0-1 |
| `<u>` gạch chân | Có (nếu reference) | Có (nếu reference) | Có (nếu reference) | Có (nếu reference) | Hiếm |
| `<span class="marker">①②</span>` | Có nếu 2+ cụm | Có nếu 2+ cụm | Có nếu 2+ cụm | Hiếm | Không |
| 注 annotation | Optional | Optional | **Khuyến khích** | Hiếm | **Không** |
| Source line | Có (essay) | Có (essay) | Có (essay) | **Không** | **Không** |
| Full-width `　` | Không | Không | Không | Hiếm | **Khuyến khích** |
| Fake source | Optional | Optional | Optional | ❌ | ❌ |

### Lỗi thường gặp cần tránh

1. **Dùng `<br>` thay `<p>`** — thói quen xấu từ data gốc. Khiến CSS không indent được, khó parse.
2. **Rắc `<ruby>` trên từ đúng level** — lãng phí và làm bài trông "non-native". Chỉ furigana cho từ vượt level (xem R4 trong `rules/vocabulary.md`).
3. **Dùng dạng "Ab"** (`週かん`, `友だち`) — dân Nhật không viết vậy. Chọn 1 trong 2: full kanji + ruby HOẶC full hiragana.
4. **Thêm source line cho N4/N5** — data gốc 0% có, đừng tự thêm.
5. **Thêm annotation cho N5** — 0% data có, đừng thêm.
6. **Quên full-width space ở N5** — bài N5 đọc khó nếu không có `　` giữa cụm từ.
7. **Tên tác giả thật** — dùng `村上春樹`, `夏目漱石` → chạm IP. Luôn tự chế tên.
8. **Marker không khớp câu hỏi** — đề có `<u>このような</u>` nhưng câu hỏi hỏi về cụm khác.
9. **Blank format không nhất quán** — đề dùng `[ ① ]` nhưng câu hỏi dùng `（ 1 ）`.
