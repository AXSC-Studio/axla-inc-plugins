---
name: intake
description: Part of Axla Legal, normally called from /axla-legal:loop. Receives a contract (or the other party's reply version), sets the contract ID and ledger row, and registers the counterparty for the guardrails. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。契約書（または相手の返事の版）を受け取り、契約 ID と台帳の1行を作り、柵のために相手を登録する。
---

# intake（受け取る）

道具：`${CLAUDE_PLUGIN_ROOT}/scripts`（Bash ではこの絶対パスを使う）。決まりは spec の「入口（トリガー）」「版の決まり」と [docs/register.md](${CLAUDE_PLUGIN_ROOT}/docs/register.md)。

1. 原本を受け取る。パスワード付き zip は `intake_ppap.py`（パスワードは引数にしない）。決まりが分からなければ人に聞く。
2. 契約 ID を決める（`yymmdd_種類_連番`）。記録フォルダ `loop/legal/contracts/<契約 ID>/` を作る。使う側の .gitignore に `loop/legal/contracts/` が無いと道具が止まるので、そのときは足してよいかを人に聞く。
3. 相手を登録する：`python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/gate.py watch <記録フォルダ> --to <相手のアドレス> --thread <threadId> --message <messageId>`。返事が別スレッドで来たら足す。
4. 台帳 `loop/legal/register.csv` に1行（相手の名前は書かない）。原本は Drive の契約フォルダに、版の名前で置く。
5. 相手の返事の版なら、版の Y を上げる。相手の変更履歴・コメント・文書のプロパティを `view.py changed` で確かめる。
6. 終わったら /axla-legal:loop に戻る。
