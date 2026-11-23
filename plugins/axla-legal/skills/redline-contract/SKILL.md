---
name: redline-contract
description: Part of Axla Legal, normally called from /axla-legal:loop. Writes your proposed changes into the other party's contract as tracked changes, with a comment giving the reason for each change, following LEGAL.md. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。LEGAL.md に沿って、相手の契約書に修正案を変更履歴で入れ、修正ごとの理由をコメントで付ける。
---

# redline-contract（直す）

契約の仕事を最初から頼まれたときは、/axla-legal:loop から始める（いまどこかを道具が決める）。

道具：`${CLAUDE_PLUGIN_ROOT}/scripts`（Bash ではこの絶対パスを使う。`${CLAUDE_PLUGIN_ROOT}` は Bash の中では置き換わらない）。手順の細部は [scripts/README.md](${CLAUDE_PLUGIN_ROOT}/scripts/README.md) の手順 1〜6。

1. `loop/legal/LEGAL.md` を全文読む（書き換えない）。自社名・作成者名は `loop/legal/config.json`（無ければ `templates/config.json` を写して埋めてもらうよう人に頼む）。
2. 原本を作業フォルダに展開し、段落の ID を調べて、`<記録フォルダ>/Redline Data.json` に直しとコメントを書く（1往復で締結できる量に絞る）。
3. `redline.py` で変更履歴を入れる（Google ドキュメント製の雛形の包みは道具が外す）。`add_comments.py` で理由のコメントを入れる。
4. 形式を検査する（docx スキルの validate.py）。
5. /axla-legal:loop に戻る（次は review）。

## 守ること
- 契約ごとの記録は `loop/legal/contracts/<契約 ID>/` に置き、git に入れない。使う側のリポジトリの .gitignore に `loop/legal/contracts/` が無ければ、道具（gate.py）が止まる。足してよいかを人に聞く。
- LEGAL.md の外の判断は G1 として人に上げる。
