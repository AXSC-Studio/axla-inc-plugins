# Axla Marketing (`axla-marketing`)

**English** | [日本語](#日本語)

When a topic comes to mind, talk about it alone in a Google Meet instead of writing notes. When you leave the meeting, the plugin turns the Gemini notes into a draft article and an eye-catch image. A person only presses "publish".

```
Talk alone in a Meet and leave
  → a watcher (Apps Script) finds the notes by document ID
  → a routine edits the talk into an article, and a reviewer checks it
  → builds the eye-catch image and the draft JSON
  → your own system puts it into your CMS as a draft and notifies you
  → a person presses publish
```

## What is inside
| Path | Contents |
|---|---|
| `skills/meeting-to-article/` | The skill (entry point) |
| `specs/marketing-001-turn-meeting-into-article.md` | The rules |
| `prompts/editor-prompts.md` | Instructions for the editor and the reviewer |
| `scripts/` | The watcher Apps Script, the draft JSON, a text-only eye-catch |

## What you put in your repository
Plugins contain tools only. Your data lives in the using repository under `loop/meet-to-article/`.

- `config.json`: meeting title, category, length, eye-catch colors and so on (example in `scripts/README.md`)
- `glossary.md`: fixes for common transcription errors
- `tone/`: sample articles whose tone you want to follow

## Principles
- Keep the energy of the talk. Edit, do not summarize. Never add what was not said.
- Automate up to the draft. A person presses publish.
- Do not rename or move the notes file (it is tracked by ID).

## License
MIT

---

## 日本語

ふと浮かんだテーマを、メモにせず一人の Google Meet でしゃべる。退出したら、Gemini メモから記事の下書きとアイキャッチまで自動で作る。公開ボタンだけ人が押す。

```
一人の Meet でしゃべって退出
  → 見張り（Apps Script）がメモをドキュメント ID で見つける
  → ルーティンが、しゃべりを編集して記事にし、検証役が見る
  → アイキャッチと下書きの JSON を作る
  → 利用側の仕組みで CMS に下書きとして入れ、通知する
  → 人が公開を押す
```

### 入っているもの
| 場所 | 中身 |
|---|---|
| `skills/meeting-to-article/` | スキル（入口） |
| `specs/marketing-001-turn-meeting-into-article.md` | 決まり |
| `prompts/editor-prompts.md` | 編集役・検証役の指示文 |
| `scripts/` | 見張りの Apps Script、下書きの JSON、文字だけのアイキャッチ |

### 利用側に置くもの
プラグインは道具だけです。データは、使う側のリポジトリの `loop/meet-to-article/` に置きます。

- `config.json`：Meet の題・カテゴリ・字数・アイキャッチの色など（例は `scripts/README.md`）
- `glossary.md`：誤変換の直し方（例：「アスクの新築情報」→「axsc.me の新着情報」）
- `tone/`：まねたい記事の見本

### 大事にしていること
- しゃべりの熱を残す。要約ではなく編集にする。言っていないことは足さない。
- 下書きまでは任せる。公開は人が押す。
- メモのファイルの名前や場所は変えない（ID で追う）。

### ライセンス
MIT
