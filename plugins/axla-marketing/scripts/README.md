# scripts の使い方

Python は `python3 -I` で動かす。必要なもの：`pip install -r requirements.txt`（Pillow だけ）。

## 1. 見張り（Apps Script）

`apps-script/watch_meet_notes.gs` を、Meet を録る本人の Google アカウントの Apps Script に貼る。

1. スクリプトのプロパティに3つを人が貼る（コードにも git にも書かない）
   - `ROUTINE_URL`：クラウドのルーティンの /fire の URL
   - `ROUTINE_TOKEN`：ルーティンの API の合鍵
   - `MEETING_TITLE`：収録に使う Meet の題（例：`コラム`）
2. `install` を1回だけ手で実行する（1分ごとのトリガーができる）。Drive を読む許可を求められたら、本人が承認する。
3. ルーティンには `meeting-to-article doc_id=<ドキュメント ID>` が届く。

## 2. 記事の下書き（make_post.py）

編集役が `prompts/editor-prompts.md` の形で書いた Markdown から、CMS の下書きの JSON を作る。

```bash
python3 -I make_post.py article.md --config <利用側>/loop/meet-to-article/config.json --out-dir <記事の JSON の置き場> --date 2026-11-20
```

- status は必ず `draft`。同じ slug のファイルがあれば止める（上書きしない）。
- 字数が config の `length` から外れたら止める。
- 要確認は JSON に入れず、標準出力に出す。通知のいちばん上に貼る。

## 3. アイキャッチ（make_eyecatch.py）

文字だけのアイキャッチを作る。外の API を呼ばないので、お金はかからない。

```bash
python3 -I make_eyecatch.py --title "<題>" --date 2026-11-20 --config <利用側>/loop/meet-to-article/config.json --out eyecatch.png
```

## 利用側の config.json（例）

```json
{
  "meeting_title": "コラム",
  "category": "column",
  "sites": ["corp"],
  "author": "<書き手の ID>",
  "length": [1500, 2500],
  "thumbnail_url": "<アイキャッチの公開 URL。{slug} が記事の slug に入れ替わる>",
  "paid_apis": [],
  "eyecatch": {
    "size": [1200, 630],
    "bg": "#111111", "fg": "#ffffff", "accent": "#c8a96a",
    "label": "COLUMN",
    "font": "<日本語が出るフォントのパス。省略時は Mac のヒラギノか Noto Sans CJK>"
  }
}
```

`paid_apis` が空のあいだは、画像生成などの有料の API を使わない。
