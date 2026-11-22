---
name: legal-loop
description: 相手から届いた契約書（まず NDA）を、変更履歴とコメントで直し、相手との往復を署名まで回すときに使う。契約書の受け取り・修正案づくり・返信メールの本文づくり・台帳の更新を頼まれたとき。
---

# Legal Loop

契約書を「受け取り → 自社の直し → 相手との往復 → 署名」まで回す。

## 最初に読むもの
1. 決まり：`${CLAUDE_PLUGIN_ROOT}/specs/legal-001-run-contract-loop.md`
2. 道具の使い方：`${CLAUDE_PLUGIN_ROOT}/scripts/README.md`
3. 検証役の指示文：`${CLAUDE_PLUGIN_ROOT}/prompts/reviewer-prompts.md`
4. 利用側のデータ（いま開いているリポジトリの中）：`loop/legal/LEGAL.md`（全文を読む。書き換えない）と `loop/legal/register.csv`

## 守ること
- 契約ごとの記録は `loop/legal/contracts/<契約 ID>/` に置き、git に入れない。
- 契約書の実物は、利用側が決めた保管場所（Axla は Google ドライブの契約フォルダ）に置く。
- 送信・署名・LEGAL.md の外の判断は、人に上げる（spec の G1／送信／G2）。
- 利用側に `loop/legal/` が無いときは、作業を止めて、置き場所を人に聞く。
