---
name: intake
description: Part of Axla Legal, normally called from /axla-legal:loop. Receives a contract (or the other party's reply version), sets the contract ID and ledger row, and registers the counterparty for the guardrails. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。契約書（または相手の返事の版）を受け取り、契約 ID と台帳の1行を作り、柵のために相手を登録する。
---

# intake（受け取る）

道具：`${CLAUDE_PLUGIN_ROOT}/redline-contract/scripts`（Bash ではこの絶対パスを使う）。決まりは spec の「入口（トリガー）」「版の決まり」と [docs/register.md](${CLAUDE_PLUGIN_ROOT}/redline-contract/docs/register.md)。

1. 原本を受け取る。パスワード付き zip は `intake_ppap.py`（パスワードは引数にしない）。決まりが分からなければ人に聞く。
   - Drive のつながりの `download_file_content` や Gmail の添付の取り込みは、ファイルをセッションの一時フォルダ（tool-results）に置く。結果に出たそのパスから、`<記録フォルダ>/received/` に版の名前（例 `v0.1.0_original.docx`）で写す（git に入らない場所）。一時フォルダのままにしない。`cp` が許可されない環境では `python3 -I -c "import shutil,sys; shutil.copyfile(sys.argv[1], sys.argv[2])" <元> <先>` で写す。
   - 写したら `shasum -a 256` を Loop Log に残し、`validate_docx.py <その .docx>` で形式を確かめる。作業フォルダ W には、ここから展開する。
2. 契約 ID を決める（`yymmdd_種類_連番`）。記録フォルダ `loop/legal/contracts/<契約 ID>/` を作る。使う側の .gitignore に `loop/legal/contracts/` が無いと道具が止まるので、そのときは足してよいかを人に聞く。
3. 相手を登録する：`python3 -I ${CLAUDE_PLUGIN_ROOT}/redline-contract/scripts/gate.py watch <記録フォルダ> --to <相手のアドレス> --thread <threadId> --message <messageId>`。返事が別スレッドで来たら足す。
4. 台帳 `loop/legal/register.csv` に1行（相手の名前は書かない）。原本は Drive の契約フォルダに、版の名前で置く。
5. 相手の返事の版なら、版の Y を上げる。相手の変更履歴・コメント・文書のプロパティを `view.py changed` で確かめる。
6. 終わったら /axla-legal:loop に戻る。
