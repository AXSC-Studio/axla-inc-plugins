---
name: loop
description: Use first for any contract work (an NDA or other contract arrived, "review this contract", "what's next on the NDA", a reply came back, sending, signing). For Japanese-language contracts in .docx. Not for PDF-only contracts, general legal advice, or the signing itself. It reads where each contract stands and runs only the next step. 日本語：日本語の契約（.docx）向け。PDF だけの契約・一般的な法律相談・署名そのものには使わない。契約の仕事は、まずこれを使う（契約書が届いた・この契約を見て・NDA の次は何か・相手の返事が来た・送る・署名）。契約ごとにいまどこかを読み、次の1歩だけを進める。
---

# loop（Axla Legal の入口）

契約のループ（[spec](${CLAUDE_PLUGIN_ROOT}/redline-contract/specs/legal-001-run-contract-loop.md)）の入口。**自分で手順を選ばない。道具が決めた次の1歩だけをやる。**

道具のフォルダ（Bash ではこの絶対パスを使う。`${CLAUDE_PLUGIN_ROOT}` は Bash の中では置き換わらない）：
`${CLAUDE_PLUGIN_ROOT}/redline-contract/scripts`

## 手順
1. 利用側のリポジトリに `loop/legal/` があるかを確かめる。無ければ止めて、置き場所を人に聞く。
2. `loop/legal/LEGAL.md` を全文読む（書き換えない）。
3. どの契約かを決める。
   - 人が契約 ID（例 `261123_NDA_1`）か相手の名前を言った → その契約。
   - 言っていない → `python3 -I ${CLAUDE_PLUGIN_ROOT}/redline-contract/scripts/loop.py list` を走らせ、契約ごとの次の1歩を見せて、どれを進めるか聞く。新しい契約なら intake。
4. `python3 -I ${CLAUDE_PLUGIN_ROOT}/redline-contract/scripts/loop.py next loop/legal/contracts/<契約 ID>` を走らせる。
5. 表示された「次」の部品のスキルだけを使う：
   - `intake` → /axla-legal:intake
   - `redline-contract` → /axla-legal:redline-contract
   - `review` → /axla-legal:review
   - `gdoc` → /axla-legal:gdoc
   - `send` → /axla-legal:send
   - `learn` → /axla-legal:learn
   - 「人（…）」・`G1`・`INCIDENT` → 何もせず、人に何を待っているかを3行で知らせて止まる。
6. 部品が終わったら、もう一度 4 に戻る。「人」の段階か、人に聞くことが出たら止まる。

## 守ること
- 送信・署名・LEGAL.md の外の判断（G1）・予算の数字は人が決める。代表がチャットで「最終 OK」「送った」「署名した」と言ったときだけ、`gate.py mark` で記録する。
- 柵（Hook）が止めたら、回り道をしない。止めた理由を直す。直せなければ人に上げる（[guardrails](${CLAUDE_PLUGIN_ROOT}/redline-contract/docs/guardrails.md)）。
- 契約の本文・相手の名前は、git にも Issue にも書かない。
