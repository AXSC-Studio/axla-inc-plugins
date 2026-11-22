# legal-loop

相手から届いた契約書（まず NDA）を、Claude Code で「受け取り → 自社の直し → 相手との往復 → 署名」まで回すためのプラグインです。

## できること
- 相手の .docx に、自社の修正案を変更履歴（挿入・削除）として入れ、修正ごとの理由を Word のコメントとして付ける
- 社内の検証役（弁護士・相手の法務・形式・生成 AI 条項の4つの見方）で、送る前に直しを確かめる
- 相手へ送る清書と、返信メールの本文を道具で作る（手で書かない）
- 台帳（register.csv）で、契約ごとの状態・版・往復の回数を記録する

## 使い方
1. 入れる：`/plugin install legal-loop@axla-inc-plugins`
2. 使う側のリポジトリに `loop/legal/` を作り、自社の決まり `LEGAL.md` と台帳 `register.csv` を置く（列は [docs/register.md](docs/register.md)）
3. 「この契約書を見て」と頼むと、スキル `legal-loop` が決まり（[specs](specs/legal-001-run-contract-loop.md)）と道具（[scripts](scripts/README.md)）を読んで進める

契約書の本文と契約ごとの記録は、このプラグインにも git にも入れません。送信・署名・決まりの外の判断は、必ず人が行います。

## ライセンス
MIT
