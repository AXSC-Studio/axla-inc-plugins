# 008 · review event（次回への学び・外側ループ）

> 封じた線と結果を照らし、学びを使う人の決まり（EVENTS.md）とひな形（templates/）の直しとして PR の案にする。次の立ち上げがそれを読む

**実装**: `event-ops/skills/review-event/SKILL.md`・`scripts/judge_lines.py`（seal・judge）・`templates/lines.json`・`hooks/guard_send.py`（線を封じる前の公開を止める）・`tests/test_review.py`
**起源**: 001 の外側。ポストモーテムの型（書くきっかけを先に決める・人を責めない・レビューで閉じる）
**ステータス**: L2（実装・テスト済み。Human Judge のマージ待ち）

---

## 1. Specify
- 起動：開催日＋N日で「終了」が立ったとき。
- `judge_lines.py`：封じた線（`lines.json`。外の文書を使う会社は結果を `--results` で渡す。ハッシュは seal で register.csv に刻む）と件数を突き合わせ、線ごとに「当たり／弱い当たり（目標の 8 割以上）／外れ」を出す。封じた線は書き換えない。
- 人の判断の数＝まとめ承認の数＋記録の「開いている人の判断」の G1 の数。register.csv の `judgments` に書き、前回と比べる。
- `runs.jsonl` から、人の手の時間と判断の数を前回と比べる。減っていなければ、PR の案に「なぜ減らなかったか」を書く。
- 学びの単位は「1往復＝1つの fail_code」。同じ fail_code が2回なら、実行境界（Sandbox）か決まりに上げる案にする。
- PR の対象は使う人の `loop/marketing/event-ops/EVENTS.md` と `templates/`。マージは人。

受け入れ条件
- [x] 線ごとの判定（当たり・弱い当たり・外れ）と、前回との判断の数の差が出る（`test_judge_gives_hit_weak_and_miss`・`test_compares_judgments_with_previous_event`）
- [x] PR の案に、変更点と理由と、どの fail_code から来たかがある（`test_repeated_fail_code_becomes_a_rule_proposal`）
- [x] 封じた線のハッシュが変わっていれば判定しない。封じていない線でも判定しない（`test_judge_refuses_rewritten_lines`・`test_judge_refuses_unsealed_lines`）
- [x] 線を封じていないと、告知の公開を hook が止める（`test_publishing_is_blocked_until_lines_are_sealed`）。seal が内側の checklist の `lines` を達成にする

## 4. Tasks
- [x] judge_lines.py（seal・judge）・templates/lines.json・checklist の lines の項目
- [x] guard_send.py に「線を封じてから公開」を足した
- [x] SKILL.md（review-event）
- [ ] 人間ゲート：人の手の「時間（分）」は、まだ自動で測れていない（承認と G1 の数だけ）。測り方は最初の本番のあとに決める
