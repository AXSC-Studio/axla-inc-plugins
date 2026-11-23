---
name: learn
description: Part of Axla Legal, normally called from /axla-legal:loop. After a contract is signed, dropped, or had an INCIDENT, collects the lessons and opens a pull request that updates LEGAL.md and raises its generation. 日本語：Axla Legal の部品（ふだんは /axla-legal:loop から呼ばれる）。署名・破談・INCIDENT のあと、学びを集め、LEGAL.md を直して世代を上げる PR を出す。
---

# learn（覚える → 定義に戻す・外側のループ）

手順は spec の「外側のループ（5 → 1）」。

1. 利用側のリポジトリで、ブランチ `legal-outer/<契約 ID>` を作る（このブランチの上だけ、柵は LEGAL.md の書き換えを通す）。
2. `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/outer_loop.py collect --contract <契約 ID> --out <scratchpad の file>`。集めた文は git に入れない。
3. LEGAL.md を直す。相手の社名・人名・条文の文は書かず、一般化して書く。INCIDENT の学びには、柵にした道具の名前を添える。
4. `outer_loop.py bump` で世代を +1。変更履歴に1行。PR を出す。**マージは代表の OK（人間ゲート）。**
5. 指示文（プラグイン側）を直す学びがあれば、プラグインのリポジトリに別の PR。
6. マージされたら `gate.py mark <記録フォルダ> learned`。
