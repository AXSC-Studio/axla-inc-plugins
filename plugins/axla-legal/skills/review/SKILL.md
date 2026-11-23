---
name: review
description: Part of Axla Legal, normally called from /axla-legal:loop. Checks a redline with four independent reviewers plus a tool for clause references, and decides pass or fail by counting with a tool. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。直しを、互いを見ない検証役4体と、条・項の参照を確かめる道具で確かめ、合否は道具で数えて決める。
---

# review（確かめる・内側のループ）

道具：`${CLAUDE_PLUGIN_ROOT}/scripts`。指示文：[prompts/reviewer-prompts.md](${CLAUDE_PLUGIN_ROOT}/prompts/reviewer-prompts.md)（全文を読む）。

1. 承諾後の本文を作る：`view.py <work> accept`。
2. 参照を機械で確かめる：`check_refs.py <work> --out <W>/review-refs.md`。
3. 検証役を起動する（1周目と、本文を大きく直した周は4体を並列に、互いの結果を見せずに。小さな直しは1体に4観点）。それぞれの出力を `<W>/review-<名前>.md` に保存する。
4. 合否を道具で決めて記録する：`count_findings.py <W>/review-*.md --record <記録フォルダ>`。検証役の書いた件数と合わなければ、その検証役をもう一度回す。参照の誤りは、検証役の重さにかかわらず致命的。
5. 周回を数える：`budget.py cycle <記録フォルダ> --version vX.Y.Z`。
6. Loop Log の「各周の記録」に、検証役ごとの件数と指摘を書く（どの版の指示文で検証したかも）。
7. /axla-legal:loop に戻る（NG なら redline-contract、OK なら gdoc に進む）。
