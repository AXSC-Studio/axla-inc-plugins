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
3. Ask "Please review this contract". The skill `redline-contract` (`/axla-legal:redline-contract`) reads the rules ([specs](specs/legal-001-run-contract-loop.md)) and the tools ([scripts](scripts/README.md)) and proceeds

Contract text and per-contract records never go into this plugin or into git. Sending, signing and any decision outside your rules are always done by a person.

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
3. 「この契約書を見て」と頼むと、スキル `redline-contract`（`/axla-legal:redline-contract`）が決まり（[specs](specs/legal-001-run-contract-loop.md)）と道具（[scripts](scripts/README.md)）を読んで進める

契約書の本文と契約ごとの記録は、このプラグインにも git にも入れません。送信・署名・決まりの外の判断は、必ず人が行います。

### 柵（Hook）
頼むだけでなく、道具で止めます。契約の相手へのメールの送信、清書の検査が通る前や画像・添付のある返信の下書き、下書きの確認が通る前にターンを終えること、中間ループの間の `LEGAL.md` の書き換え、契約の記録の `git add` を止めます。くわしくと、利用側の設定の見本は [docs/guardrails.md](docs/guardrails.md)。

### ライセンス
MIT
