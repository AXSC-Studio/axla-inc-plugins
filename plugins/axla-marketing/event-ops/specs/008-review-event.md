# 008 · review event（次回への学び・外側ループ）

> 封じた線と結果を照らし、学びを使う人の決まり（EVENTS.md）とひな形（templates/）の直しとして PR の案にする。次の立ち上げがそれを読む

**実装**: `skills/review-event/SKILL.md`・`scripts/judge_lines.py`
**起源**: 001 の外側。ポストモーテムの型（書くきっかけを先に決める・人を責めない・レビューで閉じる）
**ステータス**: L1（spec 起票・Human Judge 確認待ち）

---

## 1. Specify
- 起動：開催日＋N日で「終了」が立ったとき。
- `judge_lines.py`：封じた線（`lines_source` か plan.md。ハッシュが封じたときと同じか確かめる）と件数を突き合わせ、線ごとに「当たり／弱い当たり／外れ」を出す。封じた線は書き換えない。
- `runs.jsonl` から、人の手の時間と判断の数を前回と比べる。減っていなければ、PR の案に「なぜ減らなかったか」を書く。
- 学びの単位は「1往復＝1つの fail_code」。同じ fail_code が2回なら、実行境界（Sandbox）か決まりに上げる案にする。
- PR の対象は使う人の `loop/marketing/event-ops/EVENTS.md` と `templates/`。マージは人。

受け入れ条件
- [ ] 線ごとの判定と、前回との差の表が出る
- [ ] PR の案に、変更点と理由と、どの fail_code から来たかがある
- [ ] 封じた線のハッシュが変わっていない

## 4. Tasks
- judge_lines.py → SKILL.md
