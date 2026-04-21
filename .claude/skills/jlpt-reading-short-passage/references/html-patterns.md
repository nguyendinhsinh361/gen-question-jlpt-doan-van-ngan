# HTML Patterns — Đoạn Văn Ngắn

Template HTML cụ thể cho từng level, marker conventions, source-line format. Dùng song song với `sample-analysis.md` (phân tích định lượng) và SKILL.md (rule tổng quát).

## 1. Base Template (tất cả level)

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

`{BODY_CONTENT}` được thay thế theo level (xem các section dưới).

## 2. Template Per Level

### N1 — Formal essay/phê bình, annotation + source

Use case: essay triết học, phê bình văn hóa, bài báo formal.

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

Điểm chính:
- 2 paragraph max
- 0-1 `<ruby>` (bài N1 ít cần furigana)
- Annotation cho thuật ngữ chuyên ngành
- Source line `（[fake author]「[fake title]」による）`
- Dùng marker ①②③④ + `<u>` khi câu hỏi là reference/meaning

### N2 — Tiểu luận/phê bình nhẹ, marker đa số

Use case: tiểu luận đời sống, phê bình văn hóa, bài báo.

```html
<div class="passage">
    <p>男の<span class="marker">①</span><u>古典的な勘違い</u>の最たるものは、
    女性は家事が嫌いではないという手前勝手な信仰だろう。誤解である。
    女性の十中八九は、家事が大嫌いなのである。嫌いだが、それが仕事だし、
    ほかにやる人がいないから、<span class="marker">②</span><u>仕方なしにやる</u>。</p>
    <p>「手伝え」と言ったって、夫は連日仕事で忙しい。結局、手伝ってもらえない
    日常が続き、家事は女性の肩にのしかかる。</p>
    <p class="source">（佐藤花子「暮らしの言葉」文春社による）</p>
</div>
```

Điểm chính:
- 2-3 paragraph
- Marker ①② + `<u>` khi có reference question
- 0-2 `<ruby>` (chỉ vượt level)
- Source line phổ biến (6% data)

### N3 — Giai thoại/tư vấn, annotation nhiều

Use case: giai thoại gia đình, tư vấn, bài báo ngắn.

```html
<div class="passage">
    <p>我が家では「バカ」という言葉を使ってはいけないという<ruby>禁止令<rt>きんしれい</rt></ruby>を
    出しました。何気なく口に出していた言葉、ついつい使ってしまいます。</p>
    <p>ある時<u>「バ」まで言ってから気がついて</u>、子供はその後「……ビブベボ」。
    私は「バ……バン、バン、バン」と続けてごまかしました。</p>
    <p>怒っていた気持ちが笑いに変わり、家族みんなで大笑いしました。
    言葉を選ぶという注1行為が、こんなにも家庭を明るくするとは思いませんでした。</p>
    <div class="annotations">
        <p>注1 行為：何かをすること</p>
    </div>
</div>
```

Điểm chính:
- 3 paragraph là sweet spot
- 0-3 `<ruby>` (từ N2+ phải có furigana)
- Annotation 注1 phổ biến (40% N3 samples có)
- `<u>` quanh cụm từ được hỏi khi question = reference/meaning

### N4 — Đời sống đơn giản, ít formal

Use case: lời khuyên tiêu dùng, thông báo, hội thoại ngắn.

```html
<div class="passage">
    <p>あなたは、「買いたい」と思ったら、すぐそれを買ってしまいますか。
    買い物をするときには、まず、本当にそれに使うかどうか考えましょう。</p>
    <p>特に「安いから」と思って買ってしまうと、家にはいらない物が増えてしまいます。
    大事なのは、「いる」か「いらない」かをよく考えることです。</p>
    <p>安い物を買うのはいいことですが、使わない物を買うのは損です。</p>
    <!-- N4 không có annotation, không có source -->
</div>
```

Điểm chính:
- 3 paragraph, câu ngắn hơn N3
- 0-4 `<ruby>` nhưng nên thay bằng từ đơn giản hơn
- KHÔNG annotation, KHÔNG source line (0% data có)
- Câu hỏi thường là content_match: `どんな買い方がよくないと言っていますか。`

### N5 — Thư/lời nhắn/thông báo rất đơn giản

Use case: thư ngắn, メモ, lời nhắn.

**Option A — Letter format (hay dùng, ngoại lệ cho phép `<br>`)**:

```html
<div class="passage">
    <p class="no-indent">「ヤンさんへ<br>
    きょうは　先に　かえります。<br>
    ヤンさんに　かりた　ノートは　あした　もって　きます。<br>
    それから　わたしの　本は、まだ　つかいませんから<br>
    どうぞ　ゆっくり　よんで　ください。<br>
    　　　大川　ひろし」</p>
</div>
```

**Option B — Thông báo ngắn (không cần letter format)**:

```html
<div class="passage">
    <p>わたしは きのう としょかんへ いきました。
    ほんを ３さつ かりました。
    きょうは いえで ほんを よみます。
    あしたも よみます。</p>
</div>
```

Điểm chính:
- Full-width space `　` giữa các cụm từ (mô phỏng đề N5 thật)
- KHÔNG `<br>` trừ letter format
- 0-2 `<ruby>` (N5 bài hầu như toàn hiragana)
- KHÔNG annotation, KHÔNG source

## 3. Marker Conventions Chi Tiết

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

| Style | Level | Text in HTML | Câu hỏi |
|-------|-------|--------------|---------|
| `[ ① ]` | N1, N2 | `彼は[ ① ]と言った` | `[ ① ] に入る最も適当なものはどれか` |
| `（ 1 ）` | N2, N3 | `これは（ 1 ）問題だ` | `（ 1 ） に入る最も適当なものはどれか` |
| `　ａ　` | N3, N4 | `この花は　ａ　きれいだ` | `ａに入る最も適当なものはどれか` |

**Quy ước**:
- N1 hay dùng `[ ① ]` (fancy hơn)
- N3 hay dùng `（ 1 ）` hoặc `ａ`
- Luôn có khoảng trắng xung quanh để đọc dễ

## 4. Source Line Format

Format: `（[fake_author]「[fake_title]」[media?]による）`

| Level | Tần suất | Nên dùng |
|-------|---------|----------|
| N1    | 7/104 ≈ 7% | Có — bài essay/phê bình |
| N2    | 14/205 ≈ 7% | Có — tiểu luận/bài báo |
| N3    | 11/140 ≈ 8% | Thỉnh thoảng — essay nghiêm túc |
| N4    | 0/124 = 0%  | **KHÔNG** |
| N5    | 0/105 = 0%  | **KHÔNG** |

### Examples

```
（山田太郎「日本語の楽しみ」による）
（佐藤花子「暮らしの中の言葉」文春社による）
（鈴木一郎「現代社会論」朝日新聞による）
（田中美和子「食文化エッセイ」による）
```

### Rules

- **Author**: tên Nhật 2-4 chữ, **tự chế** (không dùng tên tác giả có thật)
- **Title**: title tự chế phù hợp chủ đề, trong dấu 「」
- **Media** (optional): `新聞`, `雑誌`, `文春社`, `月刊〇〇` — hoặc bỏ qua
- Kết thúc bằng `による）`
- **Cấm**: dùng tên tác giả có thật (村上春樹, 夏目漱石, …) vì có thể chạm IP

### Fake author pool (gợi ý)

Gender-neutral Japanese surnames + given names tự chế:
```
山田太郎, 佐藤花子, 鈴木一郎, 田中美和子, 高橋健太, 伊藤由美,
中村明, 小林さとし, 加藤けいこ, 吉田あきら, 山口まり, 斎藤ひろし
```

## 5. 注 Annotation Format

Block annotation ở cuối bài, style dashed border ngăn cách:

```html
<div class="annotations">
    <p>注1 〜〜〜：〜〜〜</p>
    <p>注2 〜〜〜：〜〜〜</p>
</div>
```

### Rules

- Đánh số `注1`, `注2`, `注3` tuần tự trong cùng bài
- Format: `注{N} {term}：{やさしい日本語で説明}` — `：` (full-width colon)
- Term là tiếng Nhật (kanji/từ khó)
- Định nghĩa **bằng tiếng Nhật đơn giản hơn** (やさしい日本語). **KHÔNG dùng tiếng Anh hay tiếng Việt** — bài đọc JLPT phải full tiếng Nhật.

### Khi nào dùng

| Level | Tần suất | Nên dùng khi |
|-------|---------|--------------|
| N1    | 19%     | Bài có thuật ngữ triết học/chuyên ngành |
| N2    | 28%     | Bài có keyword văn hóa/xã hội |
| N3    | 40%     | Bài có từ loại N2+ không thay được |
| N4    | 12%     | Ít khi — chỉ khi có từ không thể tránh |
| N5    | 0%      | **KHÔNG bao giờ** |

### Examples

```
注1 芸術：人間がつくりだす美しいもの
注1 信仰：強く信じること
注2 禁止令：してはいけないという決まり
注1 生成可能体：新しくつくり出せるもの
注1 伝統的遺産：昔から伝わる大切なもの
```

## 6. Paragraph Flow Rules

### ĐÚNG — Dùng `<p>` flow liên tục

```html
<p>芸術と日常との境界が曖昧になりつつある現代において、
俳句を文化遺産として登録することの意義を問う声が高まっている。
しかし、俳句が文学である以上、それは常に想像力によって創造され
つづける生成可能体であり、過去として凍結することは不可能である。</p>
```

Text wrap tự nhiên, không có `<br>` giữa câu. Xuống hàng trong source code chỉ để dễ đọc khi edit.

### SAI — Data gốc hay dùng `<br>`

```html
<!-- ❌ KHÔNG làm thế này trong output của skill -->
<p>芸術と日常との境界が曖昧になりつつある現代において、<br>
俳句を文化遺産として登録することの意義を問う声が高まっている。<br>
しかし、俳句が文学である以上、…</p>
```

### Ngoại lệ — N5 letter format

```html
<!-- ✅ OK cho N5 vì letter cần giữ format -->
<p class="no-indent">「ヤンさんへ<br>
きょうは　先に　かえります。<br>
…
大川　ひろし」</p>
```

## 7. Visual Elements Catalog

| Element | HTML | Khi nào dùng |
|---------|------|--------------|
| Gạch chân | `<u>…</u>` | Cụm từ được hỏi (reference/meaning) |
| Marker số | `<span class="marker">①</span>` | Bài có 2+ cụm reference |
| Furigana | `<ruby>漢字<rt>かんじ</rt></ruby>` | Chỉ cho từ vượt level |
| Blank | `[ ① ]`, `（ 1 ）`, `　ａ　` | fill_in_the_blank |
| Chú thích | `<div class="annotations">` | N1/N2/N3 với thuật ngữ |
| Source | `<p class="source">` | N1/N2/N3 bài essay/phê bình |
| Full-width space | `　` | N5 giữa cụm từ (để dễ đọc) |

## 8. Cheatsheet — "Should I include X?"

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

## 9. Lỗi Thường Gặp Cần Tránh

1. **Dùng `<br>` thay `<p>`** — thói quen xấu từ data gốc. Khiến CSS không indent được, khó parse.
2. **Rắc `<ruby>` trên từ đúng level** — lãng phí và làm bài trông "non-native". Chỉ furigana cho từ vượt level.
3. **Dùng dạng "Ab"** (`週かん`, `友だち`) — dân Nhật không viết vậy. Chọn 1 trong 2: full kanji + ruby HOẶC full hiragana.
4. **Thêm source line cho N4/N5** — data gốc 0% có, đừng tự thêm.
5. **Thêm annotation cho N5** — 0% data có, đừng thêm.
6. **Quên full-width space ở N5** — bài N5 đọc khó nếu không có `　` giữa cụm từ.
7. **Tên tác giả thật** — dùng `村上春樹`, `夏目漱石` → chạm IP. Luôn tự chế tên.
8. **Marker không khớp câu hỏi** — đề có `<u>このような</u>` nhưng câu hỏi hỏi về cụm khác.
9. **Blank format không nhất quán** — đề dùng `[ ① ]` nhưng câu hỏi dùng `（ 1 ）`.
