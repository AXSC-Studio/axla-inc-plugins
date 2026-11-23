---
name: review
description: Part of Axla Legal, normally called from /axla-legal:loop. Checks a redline with four independent reviewers plus a tool for clause references, and decides pass or fail by counting with a tool. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。直しを、互いを見ない検証役4体と、条・項の参照を確かめる道具で確かめ、合否は道具で数えて決める。
---

# review（確かめる・内側のループ）

道具：`${CLAUDE_PLUGIN_ROOT}/redline-contract/scripts`。指示文：[prompts/reviewer-prompts.md](${CLAUDE_PLUGIN_ROOT}/redline-contract/prompts/reviewer-prompts.md)（全文を読む）。

1. 承諾後の本文を作る：`view.py <work> accept`。
2. 参照を機械で確かめる：`check_refs.py <work> --out <W>/review-refs.md`。
3. 指示文の差し込みを埋める：`{OUR_PARTY_NAME}`・`{OUR_AI_USAGE}` は利用側の `loop/legal/config.json` の `our_party_name`・`ai_usage`、`{OUR_SIDE}`・`{THEIR_SIDE}` は契約書の前文（自社が甲か乙か）。config.json が無い・ひな形のままなら、止めて人に聞く。
4. 検証役を起動する（1周目と、本文を大きく直した周は4体を並列に、互いの結果を見せずに。小さな直しは1体に4観点）。それぞれの出力を `<W>/review-<名前>.md` に保存する。
5. 合否を道具で決めて記録する：`count_findings.py <W>/review-*.md --record <記録フォルダ>`。検証役の書いた件数と合わなければ、その検証役をもう一度回す。参照の誤りは、検証役の重さにかかわらず致命的。
6. 人に聞く論点を記録する：相手側の法務役が「条件付きで受ける」と見た所や、LEGAL.md の「G1 に上げる」に当たる所があれば、`gate.py mark <記録フォルダ> g1 --note '<件数と条の番号だけ。相手の名前・条文は書かない>'`。入口は、答えが出るまで止まる。
7. 周回を数える：`budget.py cycle <記録フォルダ> --version vX.Y.Z`。版は**送る直しの版**（相手の原本 vX.1.0 への直しなら vX.2.Z、相手の返事 vX.3.Z への直しなら vX.4.Z）。原本の版で数えない。
8. Loop Log の「各周の記録」に、検証役ごとの件数と指摘を書く（どの版の指示文で検証したかも）。
9. /axla-legal:loop に戻る（NG なら redline-contract、G1 があれば人を待つ、OK なら gdoc に進む）。
