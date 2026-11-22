# marketing（Axla Marketing）

ふと浮かんだテーマを、メモにせず一人の Google Meet でしゃべる。退出したら、Gemini メモから記事の下書きとアイキャッチまで自動で作る。公開ボタンだけ人が押す。

```
一人の Meet でしゃべって退出
  → 見張り（Apps Script）がメモをドキュメント ID で見つける
  → ルーティンが、しゃべりを編集して記事にし、検証役が見る
  → アイキャッチと下書きの JSON を作る
  → 利用側の仕組みで CMS に下書きとして入れ、通知する
  → 人が公開を押す
```

## 入っているもの
| 場所 | 中身 |
|---|---|
| `skills/meeting-to-article/` | スキル（入口） |
| `specs/marketing-001-turn-meeting-into-article.md` | 決まり |
| `prompts/editor-prompts.md` | 編集役・検証役の指示文 |
| `scripts/` | 見張りの Apps Script、下書きの JSON、文字だけのアイキャッチ |

## 利用側に置くもの
プラグインは道具だけです。データは使う側のリポジトリの `loop/meet-to-article/` に置きます。

- `config.json`：Meet の題・カテゴリ・字数・アイキャッチの色など（例は `scripts/README.md`）
- `glossary.md`：誤変換の直し方（例：「アスクの新築情報」→「axsc.me の新着情報」）
- `tone/`：まねたい記事の見本

## 大事にしていること
- しゃべりの熱を残す。要約ではなく編集にする。言っていないことは足さない。
- 下書きまでは任せる。公開は人が押す。
- メモのファイルの名前や場所は変えない（ID で追う）。
