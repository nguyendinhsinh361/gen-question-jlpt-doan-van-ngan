# Rules: HTML Template, Clean HTML, CSV Schema (R9, R10, R11)

> **Scope**: Đoạn văn ngắn (short-passage). **KHÔNG có screenshot PNG** — `general_image` luôn empty.

## R9. HTML Template

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{JP_TITLE_NGẮN}</title>
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
            text-indent: 1em;
        }
        .passage .no-indent { text-indent: 0; }
        .marker { font-weight: bold; color: #1e40af; }
        .annotations {
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px dashed #d1d5db;
            font-size: 0.9em;
            color: #374151;
            line-height: 1.7;
        }
        .annotations p { margin: 0.3em 0; text-indent: 0; }
        .source {
            margin-top: 1.2em;
            text-align: right;
            font-size: 0.88em;
            color: #4b5563;
            text-indent: 0;
        }
        ruby { ruby-align: center; ruby-position: over; vertical-align: baseline; }
        ruby rt { font-size: 0.55em; color: #374151; letter-spacing: 0.02em; line-height: 1; vertical-align: top; }
        u { text-decoration: underline; text-decoration-thickness: 1.5px; }
    </style>
</head>
<body>
<div class="passage">
    {BODY_CONTENT}
</div>
</body>
</html>
```

### Key specs (MUST match exactly)

| Element | Value |
|---------|-------|
| Container width | `max-width: 640px` |
| Container margin | `margin: 0 auto` (căn giữa) |
| Background body | `#f9fafb` (light gray) |
| Container background | `#fff` với `border: 1px solid #e5e7eb` |
| `word-break` | `keep-all` (xuống dòng ở ranh giới từ) |
| `text-align` | default (left) — KHÔNG justify |
| Tailwind CDN | ❌ KHÔNG dùng — CSS inline hết |
| Screenshot PNG | ❌ KHÔNG có |

### Template per level (chi tiết xem `references/html-patterns.md`)

**N1** — Formal essay/phê bình + annotation + source:
```html
<div class="passage">
    <p>芸術（注1）と日常との<ruby>境界<rt>きょうかい</rt></ruby>が曖昧になりつつある現代において、
    俳句を文化遺産として登録することの意義を問う声が高まっている。しかし、俳句が文学である以上、
    それは常に<u>①想像力によって創造されつづける生成可能体</u>であり、過去として凍結することは
    不可能である。</p>
    <p>遺産化がもたらす結果は、俳句の滅びの道しか約束しないだろう。</p>
    <div class="annotations">
        <p>注1 芸術：人間がつくりだす美しいもの</p>
    </div>
    <p class="source">（山田太郎「言葉の風景」文化新聞による）</p>
</div>
```

**N5** — Letter format (ngoại lệ cho phép `<br>`):
```html
<div class="passage">
    <p class="no-indent">「ヤンさんへ<br>
    きょうは　先に　かえります。<br>
    ヤンさんに　かりた　ノートは　あした　もって　きます。<br>
    　　　大川　ひろし」</p>
</div>
```

---

## R10. Clean HTML

### Clean HTML (`text_read`)

Strip all attributes, classes, and excess whitespace cho CSV column `text_read`. Clean HTML **GIỮ** `<ruby>` tag nhưng **BỎ** nội dung `<rt>` — nghĩa là chỉ có kanji gốc + okurigana, không có furigana trong CSV.

```python
class CleanHTMLExtractor(HTMLParser):
    SKIP_TAGS = ('style', 'script', 'rt')   # bỏ furigana trong CSV text_read
    def __init__(self):
        super().__init__()
        self.result, self.skip_depth = [], 0
        self.in_body, self.body_done = False, False
    def handle_starttag(self, tag, attrs):
        if tag == 'body': self.in_body = True; return
        if not self.in_body or self.body_done: return
        if tag in self.SKIP_TAGS: self.skip_depth += 1; return
        if self.skip_depth > 0: return
        self.result.append(f'<{tag}>')
    def handle_endtag(self, tag):
        if tag == 'body': self.body_done = True; return
        if not self.in_body or self.body_done: return
        if tag in self.SKIP_TAGS: self.skip_depth -= 1; return
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

### Character count (`count_body_chars()`)

```python
from html.parser import HTMLParser
import re

class BodyTextExtractor(HTMLParser):
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
    return len(re.sub(r'[ \t\n\r\u3000]', '', ''.join(ext.texts)))
```

Rules:
- Count từ **full HTML file**, KHÔNG phải clean HTML.
- Skip `<rt>` (furigana), `<style>`, `<script>` content.
- Remove all whitespace: space, tab, newline, full-width space (`　`).
- Numbers, punctuation, Latin chars ALL count.

### ⛔ KHÔNG có screenshot

Đoạn văn ngắn KHÔNG chụp PNG. CSV column `general_image` LUÔN empty string (`""`). Không cần Playwright / viewport / `screenshot.py` — skill này KHÔNG bundle screenshot script.

---

## R11. CSV Schema & File Naming

45 columns matching `rules/question_sheet.csv`:

| Column | Value cho đoạn văn ngắn |
|--------|-------------------------|
| `_id` | `{LEVEL}_{uuid.uuid4().hex}` — 32-char hex |
| `level` | `N1`, `N2`, `N3`, `N4`, `N5` |
| `tag` | Topic tiếng Anh slug từ catalog trong `rules/content.md` R1 (VD: `daily life`, `economics`, `culture`) |
| `jp_char_count` | Result of `count_body_chars()` |
| `kind` | **Always `đoạn văn ngắn`** |
| `general_audio` | `""` (empty) |
| `general_image` | **`""` (empty — KHÔNG có PNG)** |
| `text_read` | Clean HTML (no attributes, no `<rt>` content, collapsed whitespace) |
| `text_read_vn` | `""` (empty) |
| `text_read_en` | `""` (empty) |
| `question_label_1` | Một trong 7 labels (xem `rules/questions.md` R5) |
| `question_1` | Câu hỏi tiếng Nhật |
| `question_image_1` | `""` (empty) |
| `answer_1` | 4 options ngăn cách `\n`, KHÔNG số thứ tự |
| `correct_answer_1` | Integer `1`-`4` |
| `explain_vn_1` | Giải thích VN 3 phần (xem `rules/questions.md` R6) |
| `explain_en_1` | Giải thích EN 3 phần (cùng nội dung với VN) |
| `question_2` .. `question_5` | `""` (empty) — đoạn văn ngắn chỉ có 1 câu |
| `question_label_2` .. `question_label_5` | `""` |
| `answer_2` .. `answer_5` | `""` |
| `correct_answer_2` .. `correct_answer_5` | `""` |
| `explain_vn_2` .. `explain_vn_5` | `""` |
| `explain_en_2` .. `explain_en_5` | `""` |

### File Naming

All files và CSV `_id` column dùng cùng ID: `{LEVEL}_{uuid}`

- **Pattern**: `{LEVEL}_{uuid}.html` — e.g. `N3_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5.html`
- **Level prefix UPPERCASE**: `N1`, `N2`, `N3`, `N4`, `N5`
- **UUID**: 32-char hex từ `uuid.uuid4().hex` (full, không cắt)
- **_id in CSV** = cùng value = filename without extension

```python
import uuid
def gen_id(level: str) -> str:
    return f"{level}_{uuid.uuid4().hex}"
```

### ⛔ KHÔNG BAO GIỜ sửa CSV bằng tay

> **Nội dung câu hỏi thường chứa commas (ví dụ `100,000円`, `それは、そうだ`) → sẽ vỡ cột CSV khi mở bằng text editor thô.**
> **LUÔN dùng `scripts/fill_qa.py`** để điền Q&A — script tự quote đúng mọi trường hợp.
> Hoặc dùng `scripts/process_html.py` với `--question`/`--answers`/... args.

---

## QC Automation Scripts

```python
import re
from pathlib import Path

def check_html(html_path: str, level: str) -> dict:
    """Kiểm tra tự động các tiêu chí đo được cho đoạn văn ngắn."""
    html = Path(html_path).read_text(encoding='utf-8')
    results = {}
    
    # TC1: Character count (min AND max)
    char_count = count_body_chars(html)
    char_range = {
        "N1": (220, 260), "N2": (240, 290), "N3": (220, 290),
        "N4": (180, 240), "N5": (100, 160)
    }
    hard_reject = {"N1": 200, "N2": 200, "N3": 200, "N4": 150, "N5": 80}
    lo, hi = char_range[level]
    results["TC1_chars"] = {
        "count": char_count, "range": f"{lo}-{hi}",
        "pass": lo <= char_count <= hi + 30,
        "hard_reject": char_count < hard_reject[level]
    }
    
    # TC2: Flow text (no 。<br>)
    br_in_prose = len(re.findall(r'。\s*<br\s*/?>', html))
    results["TC2_flow_text"] = {"br_in_prose": br_in_prose, "pass": br_in_prose == 0}
    
    # TC3: Container CSS
    has_max_width = bool(re.search(r'max-width:\s*640px', html))
    has_margin_auto = bool(re.search(r'margin:\s*0\s+auto', html))
    results["TC3_container"] = {"pass": has_max_width and has_margin_auto}
    
    # TC4a: Ruby count
    ruby_count = len(re.findall(r'<ruby>', html))
    results["TC4_ruby_count"] = {"count": ruby_count}
    
    # TC4b: Wrong furigana format (check parentheses)
    paren_furigana = re.findall(r'[\u4e00-\u9fff]+[（(][ぁ-ん]+[）)]', html)
    bracket_furigana = re.findall(r'[\u4e00-\u9fff]+【[ぁ-ん]+】', html)
    results["TC4_furigana_format"] = {
        "paren_found": paren_furigana,
        "bracket_found": bracket_furigana,
        "pass": len(paren_furigana) == 0 and len(bracket_furigana) == 0
    }
    
    # TC4c: Ruby without rt (check each <ruby>...</ruby> block has <rt> inside)
    ruby_blocks = re.findall(r'<ruby>(.*?)</ruby>', html, re.DOTALL)
    ruby_without_rt = [b for b in ruby_blocks if '<rt>' not in b]
    results["TC4_ruby_has_rt"] = {
        "missing_rt": ruby_without_rt,
        "pass": len(ruby_without_rt) == 0
    }
    
    return results
```

---

## Bundled Scripts

```bash
# Đếm ký tự:
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py --count-only --file <html-file>

# Validate batch (Target Range + broken ruby):
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py --validate --html-dir assets/html/doan_van_ngan

# Full pipeline (tạo CSV row + Q&A):
python3 .claude/skills/jlpt-reading-short-passage/scripts/process_html.py \
    --file <html-file> \
    --csv sheets/samples_v1.csv \
    --tag "daily life" \
    --question-label question_content_match \
    --question "..." \
    --answers "A1|A2|A3|A4" \
    --correct 2 \
    --explain-vn "..." \
    --explain-en "..."

# Safe Q&A filling (khuyến khích cho agent — tránh vỡ CSV):
python3 .claude/skills/jlpt-reading-short-passage/scripts/fill_qa.py \
    --csv sheets/samples_v1.csv \
    --row-id N3_abcdef... \
    --question-label question_content_match \
    --q1 "..." \
    --a1 "Option 1
Option 2
Option 3
Option 4" \
    --ca1 2 \
    --evn1 "..." \
    --een1 "..."

# Load reference samples để calibrate style:
python3 .claude/skills/jlpt-reading-short-passage/scripts/load_references.py --level N3 --count 3
```
