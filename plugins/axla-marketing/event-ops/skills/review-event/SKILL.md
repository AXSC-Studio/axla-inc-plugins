---
name: review-event
description: Use after an in-person event you host has closed (teardown, settlement and thank-you done) to run the learning loop — judge the sealed targets against the results (hit, weak hit, miss) and refuse targets rewritten after sealing, compare the number of human decisions with the previous event, turn failures that happened twice into rule proposals, and draft a pull request to the user's EVENTS.md and templates that the next plan-event will read. Use when asked to review or learn from an event, or when an event has just been closed. 日本語：イベントが閉じたあと（撤収・精算・お礼が済んだあと）に、学びのループ（外側）を回すときに使う。封じた目標の線と結果を照らし（当たり・弱い当たり・外れ。封じたあとに書き換えた線では判定しない）、人の判断の数を前回と比べ、2回出た失敗を決まりの案にし、次の plan-event が読む EVENTS.md とひな形への PR の下書きを作る。
---

# review-event（外側のループ：学びで決まりを直す）

## 最初に読むもの
1. 決まり：`${CLAUDE_PLUGIN_ROOT}/event-ops/specs/008-review-event.md`（全体は 001）
2. 使う側：`loop/marketing/event-ops/EVENTS.md`・`templates/`・`register.csv`・`runs.jsonl`、そのイベントの `event-log.md`・`state.json`

道具は `S="${CLAUDE_PLUGIN_ROOT}/event-ops/scripts"`、`E=loop/marketing/event-ops/events/<ID>`。

## 手順
1. 閉じているか：`python3 "$S/close_event.py" status --event $E` が exit 0。でなければ measure-event に戻る
2. 判定：`python3 "$S/judge_lines.py" judge --event $E`（線を外の文書に置く会社は、その結果を `--results <JSON>` で渡す。外の文書は読むだけ）
   - exit 2（封じていない／書き換えられている）なら、判定せずに G1 に上げる
3. `review.md`（線と結果・人の判断の数・失敗の数）と `learning-pr.md`（決まりの案）を読み、案を具体的な文にする：
   - 同じ失敗が2回 → EVENTS.md の手順か既定値表に足す文、または実行境界（hook・config）に上げる案
   - 人の判断が減らなかった → 「なぜ減らなかったか」を、記録（event-log・runs.jsonl）から書く
   - 外れた線 → 次のイベントの線の定義か目標の見直し（今回の封じた線は変えない）
4. 使う側のリポで、`loop/marketing/event-ops/EVENTS.md` と `templates/` を直すブランチを作り、PR の下書きを出す。**マージは人**
5. プラグイン本体にも役立つ学び（どの会社にも効くもの）は、件数だけを Issue のテンプレート（spec 009）で報告する案を、人に出す

## 守ること
- 封じた線は書き換えない。PR は次のイベントのためのもの
- 実名・相手の社名は書かない（番号と件数だけ）
- main へのマージ・push は人
