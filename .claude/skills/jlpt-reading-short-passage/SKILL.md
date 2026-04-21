---
name: jlpt-doan-van-ngan
description: >
  Generate JLPT "đoạn văn ngắn" (short-passage / 短文読解) reading comprehension passages as
  styled HTML files and output CSV training data for AI fine-tuning. Each passage is a short
  Japanese prose text (80–290 characters depending on level) testing content understanding via
  a single multiple-choice question.
  This skill is specifically for the "đoạn văn ngắn" question type — NOT for "tìm thông tin"
  (information retrieval), "đoạn văn vừa", "đoạn văn dài", "đọc hiểu chủ đề", or
  "đọc hiểu tổng hợp". Unlike tìm thông tin, this skill does NOT generate screenshot PNGs.
  Use this skill whenever the user wants to: gen bài đoạn văn ngắn, tạo nội dung đoạn văn
  ngắn, generate short-passage reading comprehension, create JLPT 短文 passages,
  produce AI fine-tuning data for the đoạn văn ngắn section of JLPT N1-N5.
  Also trigger when the user mentions: gen bài đoạn văn ngắn, tạo short passage, generate
  JLPT 短文, short reading passage N1/N2/N3/N4/N5.
---

# JLPT 短文 / Đoạn Văn Ngắn — Passage Generator

This skill generates JLPT-style "short passage" (短文 / đoạn văn ngắn) reading comprehension items. These are short Japanese prose texts of 80-290 characters that test the learner's ability to grasp the main idea or a specific fact via a single multiple-choice question.

This skill covers only the "đoạn văn ngắn" type. Other reading types are outside its scope.

## Outputs Per Passage

For each passage, two artifacts are produced (**no screenshot PNG**):

1. **Styled HTML** → `assets/html/doan_van_ngan/{LEVEL}_{uuid}.html`
   Standalone page: Noto Sans JP via Google Fonts, minimal inline CSS, furigana via `<ruby>/<rt>`.
   Example: `assets/html/doan_van_ngan/N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5.html`

2. **Clean HTML** → CSV column `text_read`
   Body content only, all attributes/classes stripped, whitespace collapsed, no style/script/rt text.
   Example: `<p>日本語の授業は...</p><p>注1 あき：秋のこと</p>`

**No screenshot, no Playwright dependency.** The CSV column `general_image` is always empty.

## Character Counting (Critical — identical to other JLPT reading skills)

JLPT counts ALL visible characters (字), not just Japanese. Use this exact method:

```python
from html.parser import HTMLParser
import re

class BodyTextExtractor(HTMLParser):
    """Extracts visible text from HTML body, skipping <rt>, <style>, <script>."""
    def __init__(self):
        super().__init__()
        self.texts, self.skip_depth, self.in_body = [], 0, False
    def handle_starttag(self, tag, attrs):
        if tag == 'body': self.in_body = True
        if tag in ('rt', 'style', 'script'): self.skip_depth += 1
    def handle_endtag(self, tag):
        if tag in ('rt', 'style', 'script'): self.skip_depth -= 1
    def handle_data(self, d):
        if self.in_body and self.skip_depth == 0: self.texts.append(d)

def count_body_chars(html_string):
    ext = BodyTextExtractor()
    ext.feed(html_string)
    text = ''.join(ext.texts)
    return len(re.sub(r'[ \t\n\r\u3000]', '', text))
```

Rules:
- Count from the **full HTML file**, not the clean version
- Skip `<rt>` (furigana), `<style>`, `<script>` content
- Remove all whitespace: space, tab, newline, full-width space (　)
- Numbers, punctuation, Latin chars ALL count

Alternatively, run the bundled script:
```bash
python3 <skill-path>/scripts/process_html.py --count-only --file <html-file>
```

## Target Character Counts

### Dữ liệu tham khảo từ sample JSON (đo từ `jp_char_count`)

| Level | Samples | Min | P25 | P50 (median) | P75 | Avg | Max |
|-------|---------|-----|-----|--------------|-----|-----|-----|
| N1    | 104     | 201 | 220 | 236          | 252 | 240 | 447 |
| N2    | 205     | 202 | 238 | 258          | 291 | 273 | 645 |
| N3    | 140     | 200 | 216 | 236          | 288 | 255 | 497 |
| N4    | 124     | 151 | 181 | 202          | 235 | 216 | 438 |
| N5    | 105     | 80  | 97  | 111          | 151 | 130 | 298 |

### Target Range (BẮT BUỘC tuân thủ)

Chọn vùng P25–P75 (đảm bảo bài gen nằm giữa mainstream, không quá dài/ngắn):

| Level | Target Range | Hard Reject (< Min) |
|-------|--------------|---------------------|
| N1    | **220–260**  | < 200 → gen lại     |
| N2    | **240–290**  | < 200 → gen lại     |
| N3    | **220–290**  | < 200 → gen lại     |
| N4    | **180–240**  | < 150 → gen lại     |
| N5    | **100–160**  | < 80 → gen lại      |

After generating, always verify with `count_body_chars()`. Nếu dưới Target Range, bổ sung 1 câu văn ngắn hoặc thêm 1 chú thích `注` thay vì chấp nhận bài ngắn.

> **🚫 HARD REJECT** — Nếu `count_body_chars()` **thấp hơn Hard Reject threshold**, bài **PHẢI gen lại từ đầu**. Không chấp nhận, không chỉnh sửa nhỏ — gen lại hoàn toàn.

## Vocabulary & Grammar Constraints Per Level

- **50%+ vocabulary from the target JLPT level**
- **Never use vocabulary above the target level** without furigana
- Topic register per level:

| Level | Chủ đề | Văn phong | Cấu trúc câu |
|-------|--------|-----------|--------------|
| N5 | Nhật ký đơn giản, lời nhắn, giới thiệu rất ngắn | Thân mật, nhiều hiragana, có khoảng trắng giữa các cụm từ | ～です/～ます, ～てください |
| N4 | Mô tả đời sống, thời tiết, lịch học, lời khuyên cơ bản | Lịch sự đơn giản | ～ことができます, ～なければなりません, ～と思います |
| N3 | Bài báo ngắn, nhật ký người lớn, giai thoại, thư tư vấn | Nửa formal nửa conversational | ～について, ～によって, ～場合は, ～ために |
| N2 | Tiểu luận ngắn, email công việc, bài phê bình nhẹ, giai thoại văn hóa | Formal, văn viết | ～に伴い, ～に基づき, ～を踏まえて, ～に限り |
| N1 | Luận điểm triết học/văn hóa cô đọng, email công việc nghiêm túc, phê bình | Rất formal, văn viết cao cấp | ～いかんによらず, ～をもって, ～に先立ち, keigo |

## Furigana Rules (Critical — identical to tìm thông tin skill)

### Core Rule — Furigana Only for Above-Level Words

Furigana (`<ruby>/<rt>`) is **only** added for words/kanji that **exceed** the passage's target JLPT level. Words at or below the target level are written without furigana.

**Key principle**: A well-written passage should contain very few above-level words. Most vocabulary should be within the target level. If you find yourself adding many furigana, rewrite using simpler vocabulary instead.

### Compound Word Rule — Cấm dạng "Ab"

Khi từ có kanji vượt level, **LUÔN viết nguyên bộ kanji** rồi đặt furigana bao toàn bộ. **TUYỆT ĐỐI KHÔNG** tách nửa kanji nửa hiragana (dạng "Ab").

Chỉ chọn 1 trong 2 cách:
1. **Full kanji + furigana**: `<ruby>週間<rt>しゅうかん</rt></ruby>`
2. **Full hiragana** (ở level thấp): `しゅうかん`

**Cấm**:
- ❌ `週かん` (dạng Ab)
- ❌ `友だち` ở N5 (viết `ともだち`)
- ❌ `拠てん` (viết `<ruby>拠点<rt>きょてん</rt></ruby>`)

**Ngoại lệ Okurigana**: Từ có kanji stem + hiragana okurigana thì furigana chỉ phủ kanji, okurigana đứng riêng:
- ✅ `<ruby>届<rt>とど</rt></ruby>く` (kanji + okurigana)
- ❌ `<ruby>届く<rt>とどく</rt></ruby>` (furigana không phủ okurigana)

### Density Per Level

| Level | Above-level words | Ruby tags expected |
|-------|-------------------|-------------------|
| N5 | 0–1 | 0–2 |
| N4 | 0–2 | 0–4 |
| N3 | 0–3 | 0–6 |
| N2 | 0–2 | 0–4 |
| N1 | 0–1 | 0–2 |

> **⚠️ NGUYÊN TẮC VÀNG: THAY TỪ, KHÔNG RẮC FURIGANA**
>
> Ưu tiên:
> 1. 🥇 **Thay bằng từ cùng level** — ví dụ thay 届く (N3) bằng 来る (N5) trong bài N5
> 2. 🥈 **Viết full hiragana** (cho N5/N4)
> 3. 🥉 **Dùng furigana** — CHỈ khi không thể thay thế (tên riêng, thuật ngữ)
>
> Nếu bài có > 3 cặp `<ruby>/<rt>`, xem lại và đơn giản hóa từ vựng.

## HTML Template Skeleton

Đoạn văn ngắn dùng HTML đơn giản hơn tìm thông tin (không có A4 layout). Template chuẩn:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Passage title ngắn bằng tiếng Nhật, ví dụ: 俳句について]</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
        body {
            font-family: 'Noto Sans JP', sans-serif;
            background: #f9fafb;
            color: #111827;
            line-height: 1.9;
            word-break: keep-all;
            line-break: strict;
            overflow-wrap: break-word;
            margin: 0;
            padding: 40px 20px;
        }
        .passage {
            max-width: 640px;
            margin: 0 auto;
            background: white;
            padding: 40px 48px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            font-size: 16px;
        }
        .passage p {
            margin: 0 0 1em 0;
            text-indent: 1em;  /* Thụt đầu dòng kiểu văn Nhật */
        }
        .passage .no-indent { text-indent: 0; }
        .marker {
            font-weight: bold;
            color: #1e40af;
        }
        .annotations {
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px dashed #d1d5db;
            font-size: 0.9em;
            color: #374151;
            line-height: 1.7;
        }
        .annotations p {
            margin: 0.3em 0;
            text-indent: 0;
        }
        .source {
            margin-top: 1.2em;
            text-align: right;
            font-size: 0.88em;
            color: #4b5563;
            text-indent: 0;
        }
        ruby {
            ruby-align: center;
            ruby-position: over;
            vertical-align: baseline;
        }
        ruby rt {
            font-size: 0.55em;
            color: #374151;
            letter-spacing: 0.02em;
            line-height: 1;
            vertical-align: top;
        }
        u { text-decoration: underline; text-decoration-thickness: 1.5px; }
    </style>
</head>
<body>
<div class="passage">
    <p>[Main passage content — dùng 1 hoặc nhiều &lt;p&gt;, KHÔNG &lt;br&gt; giữa câu]</p>
    <!-- Optional: more paragraphs -->
    <p>[Additional paragraph if needed]</p>
    <!-- Optional: annotations -->
    <div class="annotations">
        <p>注1 xxx ： やさしい日本語で説明</p>
        <p>注2 xxx ： やさしい日本語で説明</p>
    </div>
    <!-- Optional: source line -->
    <p class="source">（[fake author]「[fake title]」による）</p>
</div>
</body>
</html>
```

### Layout Rules

- **Container**: `max-width: 640px`, centered, white background on light gray body
- **Font**: Noto Sans JP qua Google Fonts (KHÔNG dùng Tailwind CDN)
- **Paragraph**: `<p>` với text-indent 1em (chuẩn văn Nhật)
- **KHÔNG dùng `<br>` giữa các câu trong cùng 1 paragraph** — text phải flow liên tục
- **Ngắt paragraph** chỉ khi chuyển ý hoàn toàn khác
- **CSS chống tách từ CJK**: `word-break: keep-all; line-break: strict`
- **N5 đặc biệt**: có thể thêm khoảng trắng full-width `　` giữa các cụm từ để mô phỏng đề N5 thật (vì N5 chưa phân biệt rõ từ)

### Visual Elements Catalog (Optional)

- `<u>...</u>` — gạch chân từ/câu được hỏi (dùng cho reference/meaning question)
- `<span class="marker">①</span>`, `②`, `③`, `④` — marker cho câu hỏi tham chiếu
- `[ ① ]`, `( 1 )`, `　ａ　` — blank cho fill-in-blank question
- `<div class="annotations">` — chú thích `注1` `注2` ở cuối bài (common ở N1/N2/N3). **Giải thích PHẢI bằng tiếng Nhật đơn giản** (ví dụ: `注1 禁止令：してはいけないという決まり`). KHÔNG dùng tiếng Anh hay tiếng Việt trong bài đọc.
- `<p class="source">` — source line cuối bài (format: `（[author]「[title]」による）`)

### Marker Convention

| Loại câu hỏi | Marker trong text | Ví dụ text | Câu hỏi tham chiếu |
|--------------|-------------------|-----------|---------------------|
| Reference/meaning | `<u>...</u>` hoặc `<span class="marker">①</span>...` | `...<u>それ</u>が...` hoặc `①<u>重要なキーワード</u>` | 「それ」/「①重要なキーワード」とあるが、... |
| Fill-in-blank | `[ ① ]` hoặc `( 1 )` hoặc `　ａ　` | `...彼は[ ① ]と言った` | [ ① ] に入る最も適当なものはどれか |
| Content match (no marker) | Không cần marker | — | 筆者の考えに合うものはどれか |
| Reason (no marker) | Không cần marker | — | なぜ〜か |

### Fake Source Line Convention

Khi thêm source line, dùng format: `（[author]「[title]」による）` hoặc `（[author]「[title]」[media]による）`.

- **Author**: tên Nhật tự chế (2-4 chữ), KHÔNG dùng tên tác giả có thật
- **Title**: title tự chế phù hợp chủ đề
- **Media** (optional): `新聞`, `雑誌`, `による` hoặc bỏ qua
- Chỉ dùng cho N1/N2/N3 (theo thống kê data: N1=7/104, N2=71/205, N3=36/140, N4=0/124, N5=1/105)
- Ví dụ hợp lệ: `（山田太郎「日本語の楽しみ」朝日新聞による）`, `（佐藤花子「暮らしの中の言葉」文春社による）`

### N5 Đặc Biệt — Letter/Message Format

N5 thường dùng format thư/lời nhắn. Có thể bỏ qua CSS `.passage` và chỉ dùng `<p>` thuần với `<br>` cho các dòng của thư (đây là ngoại lệ duy nhất cho phép `<br>`).

```html
<body>
<div class="passage">
    <p class="no-indent">「ヤンさんへ<br>
    きょうは　先に　かえります。<br>
    ヤンさんに　かりた　ノートは　あした　もって　きます。<br>
    　　　大川　ひろし」</p>
</div>
</body>
```

## Clean HTML Extraction

Strip all attributes, classes, and excess whitespace for the `text_read` CSV column. Use the bundled `process_html.py` or this logic:

```python
class CleanHTMLExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result, self.skip_depth = [], 0
        self.in_body, self.body_done = False, False
    def handle_starttag(self, tag, attrs):
        if tag == 'body': self.in_body = True; return
        if not self.in_body or self.body_done: return
        if tag in ('style', 'script', 'rt'): self.skip_depth += 1; return
        if self.skip_depth > 0: return
        self.result.append(f'<{tag}>')
    def handle_endtag(self, tag):
        if tag == 'body': self.body_done = True; return
        if not self.in_body or self.body_done: return
        if tag in ('style', 'script', 'rt'): self.skip_depth -= 1; return
        if self.skip_depth > 0: return
        self.result.append(f'</{tag}>')
    def handle_data(self, data):
        if not self.in_body or self.body_done or self.skip_depth > 0: return
        self.result.append(data)

def clean_html(full_html):
    ext = CleanHTMLExtractor()
    ext.feed(full_html)
    raw = ''.join(ext.result)
    raw = re.sub(r'\s+', ' ', raw)
    raw = re.sub(r'\s*<', '<', raw)
    raw = re.sub(r'>\s*', '>', raw)
    raw = re.sub(r'<(\w+)></\1>', '', raw)
    return raw.strip()
```

**Note**: Clean HTML giữ lại `<ruby>` nhưng BỎ nội dung `<rt>` (để test_read chỉ có kanji gốc + okurigana, không có furigana).

## Question Generation

Each passage includes exactly **1 multiple-choice question** at all levels (N1-N5). This is the defining feature of "đoạn văn ngắn" — single-question passages.

### Question Count Per Level

| Level | Questions per passage |
|-------|----------------------|
| N1 | 1 |
| N2 | 1 |
| N3 | 1 |
| N4 | 1 |
| N5 | 1 |

CSV columns `question_2` through `question_5` are left empty.

### Question Label Distribution (from mission.json, based on data patterns)

Use `question_label_1` from this catalog — pick based on question intent:

| `question_label` | Khi nào dùng | Ví dụ keywords trong câu hỏi |
|-------------------|--------------|-------------------------------|
| `question_content_match` | Chọn câu phù hợp với nội dung | 最も合っているもの, 正しいもの, 本文の内容と合うもの |
| `question_reason_explanation` | Hỏi lý do / nguyên nhân | なぜ, どうして, ～のはなぜか |
| `question_reference` | Hỏi đại từ chỉ định | それ, これ, その, この, どんな〜か |
| `question_meaning_interpretation` | Hỏi nghĩa của câu/cụm từ | どういうことか, どういう意味か |
| `question_content_mismatch` | Chọn câu KHÔNG phù hợp | 合わないもの, 正しくないもの, 間違っているもの |
| `question_author_opinion` | Hỏi quan điểm tác giả | 筆者の考え, 筆者は...と思っているか |
| `question_fill_in_the_blank` | Điền từ vào ô trống | [ ① ] に入る, ( 1 ) に入る最も適当なもの |

**Distribution đề xuất per level** (để batch đa dạng):

| Level | Nên dùng nhiều | Hạn chế dùng |
|-------|-----------------|--------------|
| N5 | content_match, reference, reason_explanation | author_opinion, meaning_interpretation (quá khó) |
| N4 | content_match, reference, reason_explanation, content_mismatch | author_opinion (quá khó) |
| N3 | Tất cả trừ ít dùng author_opinion | — |
| N2 | Tất cả, đặc biệt author_opinion, meaning_interpretation | — |
| N1 | author_opinion, meaning_interpretation, reason_explanation | content_mismatch (quá đơn giản) |

> **BẮT BUỘC trong batch > 3 bài**: Không dùng cùng 1 `question_label` cho tất cả bài. Phân bổ đa dạng.

### Question Quality Rules

1. **Câu hỏi phải answer được từ trong bài** — không yêu cầu suy luận ngoài bài hoặc kiến thức nền.
2. **4 đáp án plausible** — mỗi distractor phải có liên quan tới nội dung bài, nhưng sai ở 1 chi tiết hoặc hiểu nhầm ý.
3. **Chỉ 1 đáp án đúng**: kiểm tra kỹ, không có 2 đáp án cùng đúng.
4. **Distractor quality theo level**:
   - N5: sai rõ ràng (thông tin ngược lại / không có trong bài)
   - N4: sai ở 1 chi tiết (thời gian, đối tượng)
   - N3: sai ở 1 nuance (đảo ngược quan hệ, đảo ngược nhân-quả)
   - N2: sai ở 1 giải thích (chọn lý do không chính xác)
   - N1: sai tinh vi — đúng 2/3 ý, sai 1 ý khó nhận ra
5. **Furigana trong câu hỏi**: Cùng rule với bài đọc — chỉ cho từ vượt level. Câu hỏi thường dùng vocab level-appropriate, nên ít cần furigana.
6. **Không có ảnh trong câu hỏi** — `question_image_1` luôn empty.

### Answer Format in CSV

Mỗi `answer_{i}` chứa 4 options ngăn cách bởi `\n`, **KHÔNG có số thứ tự** trước mỗi đáp án:
```
Option A text\nOption B text\nOption C text\nOption D text
```

**⚠️ KHÔNG dùng** `1. `, `2. `, `3. `, `4. ` trước đáp án. Chỉ cần nội dung thuần.

`correct_answer_{i}` là số `1`, `2`, `3`, hoặc `4` (chỉ số thứ tự đáp án đúng, đếm từ 1).

**CHÚ Ý**: Data gốc JSON dùng `correctAnswer` index 0-based. Khi convert sang CSV, phải +1 → `correct_answer_1` = index + 1.

## CSV Schema

Dùng schema 45 cột chuẩn từ `rules/question_sheet.csv`. Các cột quan trọng:

| Column | Value for this skill |
|--------|----------------------|
| `_id` | `{LEVEL}_{uuid}` — e.g. `N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5`. Generate UUID with `uuid.uuid4().hex` (full 32-char hex) |
| `level` | `N1`, `N2`, `N3`, `N4`, `N5` |
| `tag` | Topic label (VD: `kinh tế`, `văn hóa`, `y học`, `xã hội`, `công nghệ`, `nhật ký`, `thư từ`, `trường học`, `hội thoại hàng ngày`) — chọn từ `rules/topic.json` hoặc tự define |
| `jp_char_count` | Result of `count_body_chars()` trên full HTML |
| `kind` | Always `đoạn văn ngắn` |
| `general_audio` | "" (empty string) |
| `general_image` | "" (empty string — khác với tìm thông tin) |
| `text_read` | Clean HTML (no attributes, collapsed whitespace, no `<rt>` text) |
| `text_read_vn` | "" (empty — Phase sau nếu cần) |
| `text_read_en` | "" (empty — Phase sau nếu cần) |
| `question_label_1` | One of the labels above (content_match, reason_explanation, reference, ...) |
| `question_1` | Câu hỏi tiếng Nhật (furigana chỉ cho từ vượt level) |
| `question_image_1` | "" |
| `answer_1` | 4 options ngăn cách `\n` (KHÔNG số thứ tự): `optionA\noptionB\noptionC\noptionD` |
| `correct_answer_1` | Số `1`, `2`, `3`, `4` |
| `explain_vn_1` | Giải thích tiếng Việt tại sao đáp án đúng + tại sao 3 đáp án kia sai |
| `explain_en_1` | Giải thích tiếng Anh (cùng nội dung với explain_vn_1) |
| `question_2` .. `question_5` | "" (empty) — đoạn văn ngắn chỉ có 1 câu |
| `question_label_2` .. `question_label_5` | "" |
| `answer_2` .. `answer_5` | "" |
| `correct_answer_2` .. `correct_answer_5` | "" |
| `explain_vn_2` .. `explain_vn_5` | "" |
| `explain_en_2` .. `explain_en_5` | "" |

## File Naming & _id Convention

All files and the CSV `_id` column use the same ID: `{LEVEL}_{uuid}`

- **Pattern**: `{LEVEL}_{uuid}.html` — e.g. `N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5.html`
- **Level prefix UPPERCASE**: `N1`, `N2`, `N3`, `N4`, `N5`
- **UUID**: 32-char hex từ `uuid.uuid4().hex` (full, không cắt)
- **_id in CSV** = same value = filename without extension

```python
import uuid
def gen_id(level: str) -> str:
    return f"{level}_{uuid.uuid4().hex}"
```

## Generation Workflow (12 bước)

1. **Load references** — đọc 2-3 sample từ `data/doan_van_ngan_n{level}_clean.json` bằng `scripts/load_references.py --level N3 --count 3` để calibrate style
2. **Generate ID** — `{LEVEL}_{uuid4().hex}`
3. **Chọn `question_label` + topic** — đa dạng trong batch (xem distribution đề xuất)
4. **Chọn `tag` (topic)** — từ `rules/topic.json`, không trùng trong batch
5. **Gen HTML** — theo template, đúng char range, furigana rules, marker nếu cần
6. **Count chars** — `count_body_chars()`, hard reject nếu < threshold
7. **Save HTML** — `assets/html/doan_van_ngan/{LEVEL}_{uuid}.html`
8. **Extract clean HTML** — dùng `process_html.py` → cột `text_read`
9. **Gen câu hỏi** — 1 câu, 4 đáp án (KHÔNG số thứ tự), marker khớp với text, chỉ 1 correct
10. **Gen explain VN + EN** — giải thích tại sao đúng + tại sao các đáp án khác sai
11. **Điền CSV** — 45 cột, `kind`=`đoạn văn ngắn`, `general_image`="", `question_2-5` empty
12. **Append vào `sheets/` CSV** và verify bằng `process_html.py --validate`

> **🚨 QUY TẮC CSV BẮT BUỘC — KHÔNG ĐƯỢC BỎ QUA**
>
> Sau khi gen **MỖI BÀI**, PHẢI ngay lập tức:
> 1. Save file HTML vào `assets/html/doan_van_ngan/`
> 2. Chạy `process_html.py` để append row vào CSV
> 3. Verify row đã được ghi bằng cách đếm rows trong CSV
>
> **KHÔNG gen hết batch rồi mới ghi CSV** — dễ mất dữ liệu.
> Khi user yêu cầu gen N bài × M levels = tổng K bài, file CSV cuối cùng PHẢI có đúng K rows mới.
>
> Sau khi hoàn thành toàn bộ batch, chạy validate:
> ```bash
> python3 <skill>/scripts/process_html.py --validate --html-dir assets/html/doan_van_ngan
> ```

**Batch size**: tùy theo yêu cầu user. Gen từng bài, save HTML + CSV ngay, verify cuối batch.

## Reference Samples

Data mẫu có sẵn trong `data/`:

| Level | File | Samples |
|-------|------|---------|
| N1 | `doan_van_ngan_n1_clean.json` | 104 |
| N2 | `doan_van_ngan_n2_clean.json` | 205 |
| N3 | `doan_van_ngan_n3_clean.json` | 140 |
| N4 | `doan_van_ngan_n4_clean.json` | 124 |
| N5 | `doan_van_ngan_n5_clean.json` | 105 |

Mỗi sample có structure:
```json
{
  "id": 143,
  "general_text_read": "...HTML content with <br>, <p>, <ruby>...",
  "content": [
    {
      "question": "...",
      "answers": ["A1", "A2", "A3", "A4"],
      "correctAnswer": 1  // 0-based index, convert to 1-based khi save CSV
    }
  ],
  "jp_char_count": 211,
  "kind": "đoạn văn ngắn",
  "level": 3
}
```

**LƯU Ý KHI ĐỌC DATA GỐC**:
- Data gốc DÙNG `<br>` nhiều — đây là thói quen không tốt. Output HTML CỦA SKILL phải dùng `<p>` thuần, KHÔNG `<br>` giữa câu (xem Layout Rules ở trên).
- Data gốc có `<span>` bọc mỗi đoạn văn — output KHÔNG cần bọc span.
- Data gốc có `<ruby>` dùng cho cả từ đúng level (vd N4 rắc ruby trên 本当, 場所, 捨てる) — output CHỈ furigana cho từ vượt level.

Đọc sample để học **nội dung/chủ đề/question pattern**, KHÔNG bắt chước styling xấu của data gốc.

Chi tiết phân tích từng level xem `references/sample-analysis.md`.

## Topic Catalog

Chọn `tag` từ các nhóm sau (hoặc từ `rules/topic.json`):

| Nhóm | Topic labels |
|------|--------------|
| Đời sống | `nhật ký`, `thư từ`, `hội thoại hàng ngày`, `gia đình`, `ăn uống`, `sức khỏe đời sống` |
| Xã hội | `xã hội`, `văn hóa`, `truyền thống`, `môi trường`, `ngôn ngữ` |
| Công việc | `công việc`, `email công việc`, `thông báo công ty` |
| Giáo dục | `trường học`, `giáo dục`, `học tập`, `nghiên cứu` |
| Kinh tế | `kinh tế`, `tiêu dùng`, `thương mại` |
| Khoa học | `công nghệ`, `khoa học`, `y học` |
| Văn học | `tiểu luận`, `phê bình`, `triết học`, `văn học` |

Trong batch > 5 bài, chọn topic từ ≥ 3 nhóm khác nhau để đa dạng.

## Bundled Scripts

### scripts/process_html.py

Pipeline tự động: count chars + clean HTML + update CSV.

```bash
# Count chars only
python3 <skill>/scripts/process_html.py --count-only --file <html-file>

# Full pipeline: count + clean HTML + CSV append/update
python3 <skill>/scripts/process_html.py \
    --file <html-file> \
    --csv sheets/samples_v1.csv \
    --level N3 \
    --tag "nhật ký" \
    --question-label question_content_match \
    --question "..." \
    --answers "A1|A2|A3|A4" \
    --correct 2 \
    --explain-vn "..." \
    --explain-en "..."

# Process all files in a directory (recompute clean HTML + chars)
python3 <skill>/scripts/process_html.py --html-dir assets/html/doan_van_ngan --csv sheets/samples_v1.csv
```

### scripts/load_references.py

Load & pretty print sample JSON cho AI agent:

```bash
# Show stats per level
python3 <skill>/scripts/load_references.py --stats

# Pretty print 3 random samples at N3
python3 <skill>/scripts/load_references.py --level N3 --count 3

# Pretty print specific id
python3 <skill>/scripts/load_references.py --level N3 --id 143
```

## Verification Checklist Per Batch

Chạy checklist sau mỗi batch:

- [ ] Mỗi bài có `_id` unique, đúng format `{LEVEL}_{uuid}`
- [ ] `kind` = `đoạn văn ngắn` trong tất cả rows
- [ ] `general_image` = "" (empty) — không có PNG
- [ ] `general_audio` = "" (empty)
- [ ] Char count nằm trong Target Range (xem bảng)
- [ ] Không bài nào dưới Hard Reject threshold
- [ ] Từ vựng/ngữ pháp đúng level (50%+ target level)
- [ ] Furigana chỉ cho từ vượt level, không dạng "Ab"
- [ ] Ruby tags count ≤ expected (N5: 2, N4: 4, N3: 6, N2: 4, N1: 2)
- [ ] Mỗi bài có đúng 1 câu hỏi (`question_2` → `question_5` empty)
- [ ] `question_label_1` phù hợp với intent câu hỏi
- [ ] Batch có đa dạng `question_label` (≥ 2 label khác nhau nếu batch > 3 bài)
- [ ] Mỗi câu hỏi có 4 đáp án ngăn cách `\n` trong `answer_1` (KHÔNG có số thứ tự "1. ", "2. ")
- [ ] `correct_answer_1` là số 1-4
- [ ] Chỉ 1 đáp án đúng per câu (kiểm tra manual)
- [ ] Distractor quality phù hợp level
- [ ] `explain_vn_1` + `explain_en_1` đều có nội dung
- [ ] Marker trong text khớp với câu hỏi (nếu dùng ①, (1), `<u>`, blank)
- [ ] HTML text_read clean — không attribute, không class, không `<rt>` content
- [ ] `<p>` thuần, không `<br>` giữa câu (trừ N5 letter format)
- [ ] Annotation (注) giải thích bằng **tiếng Nhật đơn giản**, KHÔNG dùng tiếng Anh/Việt
- [ ] Số rows trong CSV = đúng số bài đã gen (đếm lại sau batch)
- [ ] Trong batch, không trùng chủ đề (`tag`)
