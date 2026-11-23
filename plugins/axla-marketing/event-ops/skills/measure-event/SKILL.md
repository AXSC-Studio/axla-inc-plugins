---
name: measure-event
description: Use for the day of an in-person event you host and right after it — build the run sheet (timeline, roles, checks, teardown checklist), count the roster into numbers only (registered, attended, consented) and discard names, record settlement, draft the thank-you and follow-up to attendees only (a person sends it), and close the event when teardown, settlement and the thank-you are all done, which starts the learning loop. Use when asked to prepare the day, count attendance, wrap up after the event, or send thanks. 日本語：イベントの当日と直後に使う。段取り表（時間割・係・確認・撤収の確認）を作り、名簿から件数だけを台帳に入れて名前は捨て、精算を記録し、来場者だけへのお礼とフォローアップを下書きし（送るのは人）、撤収・精算・お礼の3つがそろったらイベントを閉じて学びのループを起こす。
---

# measure-event（中間ループの終わり：当日・撤収・お礼）

## 最初に読むもの
1. 決まり：`${CLAUDE_PLUGIN_ROOT}/event-ops/specs/007-measure-event.md`（全体は 001）
2. 道具：`${CLAUDE_PLUGIN_ROOT}/event-ops/scripts/README.md`
3. 使う側：そのイベントの `plan.md`・`event-log.md` の先頭・`run-sheet.md`

道具は `S="${CLAUDE_PLUGIN_ROOT}/event-ops/scripts"`、`E=loop/marketing/event-ops/events/<ID>` として動かす。

## 当日の前
1. `run-sheet.md` の時間割を plan.md から埋める（係は役の名前で。実名は書かない）。「当日の確認」「撤収の確認」の箱は消さない
2. 会場の確定（G2）のあとなら `python3 "$S/check_kit.py" --event $E` が exit 0 であること（【仮】が残っていれば止まる）

## 当日のあと
1. 名簿を書き出し、件数だけを入れて名簿は捨てる：
   `python3 "$S/count_roster.py" --event $E --roster <名簿の CSV> --delete`
2. 撤収の確認の箱を全部 [x] にしたら：`python3 "$S/close_event.py" teardown --event $E`
3. 精算：`python3 "$S/close_event.py" settle --profit <損益> --event $E`
4. お礼の下書き：`python3 "$S/close_event.py" thanks-draft --event $E` → `kit/thanks.json`（送り先は来場者 checked_in だけ）。【】を埋め、`check_outbound.py` で確かめる
5. **人に、まとめ承認とお礼の送信を頼んで止まる**（一斉メッセージは spec 002 の hook が止める）。送る前に、来場の件数と受付の実数を人が見比べる
6. 人が送ったら：`python3 "$S/close_event.py" thanks-sent --event $E`
→ 3つがそろうとイベントが閉じ（`state.json` の closed）、外側の `review-event` の出番になる

## 守ること
- 名簿（名前・連絡先）は数えたら捨てる。台帳と記録には件数だけ
- 後日の連絡を望んだ人の連絡先は、使う側の CRM（`~~crm`）にだけ置く
- お礼を送る・一斉メッセージを出すのは人
