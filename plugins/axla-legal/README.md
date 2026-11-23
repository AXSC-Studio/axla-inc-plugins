# Axla Legal (`axla-legal`)

**English** | [日本語](#日本語)

A Claude Code plugin that runs a contract you received (starting with NDAs) from intake, through your own redline and the back-and-forth with the other party, up to signature.

## What it does
- Puts your proposed changes into the other party's .docx as tracked changes (insertions and deletions), with a Word comment explaining each change
- Checks the redline before sending, using internal reviewers with four viewpoints: your lawyer, the other party's legal team, formatting, and generative-AI clauses
- Builds the clean copy to send and the reply email body with tools, not by hand
- Records each contract's status, version and number of round trips in a ledger (`register.csv`)

## How to use
1. Install: `/plugin install axla-legal@axla-inc-plugins`
2. In the repository where you will use it, create `loop/legal/` and put your own rules `LEGAL.md` and your ledger `register.csv` there (columns are in [docs/register.md](docs/register.md))
3. Add one line to that repository's `.gitignore`: `loop/legal/contracts/` (the tools stop if it is missing)
4. Type `/axla-legal:loop` (or ask "Please review this contract"). The entry reads where each contract stands and runs only the next step: `intake` → `redline-contract` → `review` → `gdoc` → `send` → `learn`. It stops and tells you when it is waiting for a person (final OK, sending, signing)

Contract text and per-contract records never go into this plugin or into git. Sending, signing and any decision outside your rules are always done by a person.

## Try it in 5 minutes (no Google account needed)
`examples/` has a fictional NDA between two made-up companies, a sample redline (`Redline Data.json`) and a sample reviewer output. In a terminal, with `T` set to this plugin's `scripts` folder and `E` to its `examples` folder:

```bash
W=$(mktemp -d)
python3 -I -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$E/example-nda.docx" "$W/work"
python3 -I "$T/redline.py" "$W/work" "$E/Redline Data.json"        # tracked changes
python3 -I "$T/view.py" "$W/work" changed                           # see what changed
python3 -I "$T/check_refs.py" "$W/work" --out "$W/review-refs.md"   # clause references
cp "$E/review-sample.md" "$W/review-a.md"
python3 -I "$T/count_findings.py" "$W"/review-*.md                  # pass or fail, counted by a tool
python3 -I "$T/make_clean.py" "$W/work" --out "$W/clean.docx"       # the clean copy to send
python3 -I "$T/make_reply.py" "$E/Redline Data.json" --out-text "$W/reply.txt" --out-html "$W/reply.html"
```

Templates for your own repository are in `templates/` (`LEGAL.md`, `register.csv`, the `.gitignore` line).

## Example prompts
- "An NDA arrived from a new partner. `/axla-legal:loop`" — starts intake, then the redline and review.
- "The other party replied to our NDA redline. What's next? `/axla-legal:loop 261123_NDA_1`" — reads their version and runs the next round.
- "I gave the final OK. Prepare the reply draft and check it before I send." — builds the clean copy and reply, then runs the pre-send check (sending stays with you).

## Guardrails (hooks)
The plugin ships hooks that stop, instead of just asking: sending mail to a contract counterparty, creating a reply draft before the clean-copy check passes or with images or attachments, ending the turn before the draft check passes, editing `LEGAL.md` during a deal, and adding contract records to git. Details and a sample for your repository's settings: [docs/guardrails.md](docs/guardrails.md).

## License
MIT

---

## 日本語

相手から届いた契約書（まず NDA）を、Claude Code で「受け取り → 自社の直し → 相手との往復 → 署名」まで回すためのプラグインです。

### できること
- 相手の .docx に、自社の修正案を変更履歴（挿入・削除）として入れ、修正ごとの理由を Word のコメントとして付ける
- 送る前に、社内の検証役が直しを確かめる。見方は4つ（自社の弁護士・相手の法務・形式・生成 AI 条項）
- 相手へ送る清書と、返信メールの本文を道具で作る（手で書かない）
- 台帳（`register.csv`）に、契約ごとの状態・版・往復の回数を記録する

### 使い方
1. 入れる：`/plugin install axla-legal@axla-inc-plugins`
2. 使う側のリポジトリに `loop/legal/` を作り、自社の決まり `LEGAL.md` と台帳 `register.csv` を置く（列は [docs/register.md](docs/register.md)）
3. そのリポジトリの `.gitignore` に `loop/legal/contracts/` の1行を足す（無いと道具が止まる）
4. `/axla-legal:loop` と打つ（または「この契約書を見て」と頼む）。入口が契約ごとにいまどこかを読み、次の1歩だけを進める：`intake` → `redline-contract` → `review` → `gdoc` → `send` → `learn`。人を待つ所（最終 OK・送信・署名）では止まって知らせる

契約書の本文と契約ごとの記録は、このプラグインにも git にも入れません。送信・署名・決まりの外の判断は、必ず人が行います。

### 5分で試す（Google のアカウントは要らない）
`examples/` に、架空の会社どうしのダミーの NDA、直しの見本（`Redline Data.json`）、検証役の出力の見本があります。端末で、`T` にこのプラグインの `scripts` フォルダ、`E` に `examples` フォルダを入れて：

```bash
W=$(mktemp -d)
python3 -I -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$E/example-nda.docx" "$W/work"
python3 -I "$T/redline.py" "$W/work" "$E/Redline Data.json"        # 変更履歴を入れる
python3 -I "$T/view.py" "$W/work" changed                           # 変わった所を見る
python3 -I "$T/check_refs.py" "$W/work" --out "$W/review-refs.md"   # 条・項の参照
cp "$E/review-sample.md" "$W/review-a.md"
python3 -I "$T/count_findings.py" "$W"/review-*.md                  # 合否を道具で数える
python3 -I "$T/make_clean.py" "$W/work" --out "$W/clean.docx"       # 相手に送る清書
python3 -I "$T/make_reply.py" "$E/Redline Data.json" --out-text "$W/reply.txt" --out-html "$W/reply.html"
```

自社のリポジトリに置くひな形は `templates/` にあります（`LEGAL.md`・`register.csv`・`.gitignore` の1行）。

### 例のプロンプト
- 「新しい取引先から NDA が届いた。`/axla-legal:loop`」：受け取りから始め、直しと検証へ進む。
- 「NDA の直しに相手から返事が来た。次は？ `/axla-legal:loop 261123_NDA_1`」：相手の版を読み、次の往復を回す。
- 「最終 OK を出した。返信の下書きを作って、送る前に確かめて」：清書と返信文を作り、送る前の検査を通す（送信はあなたが押す）。

### 柵（Hook）
頼むだけでなく、道具で止めます。契約の相手へのメールの送信、清書の検査が通る前や画像・添付のある返信の下書き、下書きの確認が通る前にターンを終えること、中間ループの間の `LEGAL.md` の書き換え、契約の記録の `git add` を止めます。くわしくと、利用側の設定の見本は [docs/guardrails.md](docs/guardrails.md)。

### ライセンス
MIT
