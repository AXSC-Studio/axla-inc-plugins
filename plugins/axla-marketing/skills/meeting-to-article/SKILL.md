---
name: meeting-to-article
description: Use to turn the Gemini notes (transcript) of a solo Google Meet into a draft article (starting with columns) and an eye-catch image, when asked to turn a Meet recording into an article, or when the watcher Apps Script sends a Drive document ID. 日本語：一人の Google Meet で収録した Gemini メモ（文字起こし）から、サイトの記事（まずコラム）の下書きとアイキャッチを作るときに使う。「コラムのメモができた」「Meet の収録を記事にして」と頼まれたとき、または見張りの Apps Script から Drive のドキュメント ID が届いたとき。
---

# Meeting to Article

しゃべった熱が冷める前に、記事の下書きまで運ぶ。公開ボタンは人が押す。

## 最初に読むもの
1. 決まり：`${CLAUDE_PLUGIN_ROOT}/specs/marketing-001-turn-meeting-into-article.md`
2. 道具の使い方：`${CLAUDE_PLUGIN_ROOT}/scripts/README.md`
3. 編集役・検証役の指示文：`${CLAUDE_PLUGIN_ROOT}/prompts/editor-prompts.md`
4. 利用側のデータ（いま開いているリポジトリの中）：`loop/marketing/meeting-to-article.json`・`loop/marketing/glossary.md`・`loop/marketing/tone/`（全文を読む。書き換えない）

## 守ること
- メモはドキュメント ID で扱う。Drive のファイル名は変えない・動かさない（ほかの定期タスクが名前を付け替えるため）。
- 書くのは「要約」ではなく「しゃべりの編集」。本人が言っていないことは足さない。
- 荒い言葉は穏やかに言い換え、取引先の名前は伏せる。どちらも通知の「要確認」に並べる。
- 下書き（status: draft）だけを作る。既にある記事は上書きしない。公開しない。
- お金がかかる道具（画像生成の API など）は、利用側の config で許されたときだけ使う。初期値は使わない。
- 利用側に `loop/marketing/` が無いときは、作業を止めて、置き場所を人に聞く。
