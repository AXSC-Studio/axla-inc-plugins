# 003 · plan event（立ち上げ・内側ループ）

> 目的・目標の線・定員・参加費・収支・日程の候補と、資料一式を作り、checklist が全部「達成」になるまで直す。すでに動いているイベントは途中から取り込む

**実装**: `event-ops/skills/plan-event/SKILL.md`・`scripts/new_event.py`・`scripts/recalc_budget.py`・`scripts/checklist.py`・`scripts/check_kit.py`・`scripts/eventops_lib.py`・`hooks/stop_guard.py`（Stop hook）・`prompts/reviewer-prompts.md`・`templates/`・`tests/test_plan.py`
**起源**: 001 の内側。最初の実例で時間を食った「収支と日程の計算し直し」
**ステータス**: L2（実装・テスト済み。Human Judge のマージ待ち）

---

## 1. Specify
- 新しいイベントは `events/<yymmdd_英語の名前>/` を作り、ひな形を写す。使う人の `templates/` があればそちらを優先する（外側の学びがここに戻る）。
- **adopt**：すでに資料や送った履歴があるイベントは、それを v1.0 として `sent/` と `partners.csv` に取り込んでから始める。
- 収支は `recalc_budget.py`（会場費・時間・参加費・手数料の率・1人の原価 → 損益の表と赤字にならない人数）。手で計算しない。確かめていない前提には「未確認」。
- 資料一式は config の `kit` で決める（初期値：概要・スポンサー向け・会場レイアウト・告知の下書き・アイキャッチ）。形は `~~docs`・`~~events` の adapter（004）。
- 会場が決まる前の数字とレイアウトは【仮】の印を付けて合格にしてよい。G2 の記録の後に【仮】が残っていれば `check_kit.py` が exit 1 を返し、開催へ進めない。
- 目標の線は告知の公開前に封じる（数・定義・封じた日・ハッシュを register.csv に）。`lines_source` が外の文書を指すときは読むだけ。
- 呼び直し（相手の返事で条件が変わった）のときは、plan.md の差分に関わる checklist の項目だけを「未達」に戻す。

受け入れ条件
- [x] checklist.json の全項目が「未達」から始まり、達成の項目にはすべて証拠のパスがある（`test_init_creates_event_with_all_items_unmet`・`test_mark_requires_existing_evidence`）
- [x] 料金を変えて呼び直すと、損益の表が作り直され、event-log に「計画の変更」が1行増え、収支に関わる項目が未達に戻る（`test_recalc_records_change_and_resets_dependent_items`）
- [x] 検証役の項目は、スクリプトの項目が全部達成になった後にだけ達成にできる（`test_reviews_wait_for_scripts`）。致命的が 0 でなければ達成にならない
- [x] 3周で終わらなければ、Stop hook が G1 に上げて止まる（`test_stop_escalates_to_g1_after_max_rounds`。本物の Claude Code でも 2026-11-23 に確認：3回戻して4回目に G1）

## 2. Plan 外部設計
- `/axla-marketing:plan-event`（新規・呼び直し・adopt を自分で見分ける）。
- 内側のループはコードが回して止める：`checklist.py start` で始めると、Stop hook（`hooks/stop_guard.py`）が、checklist に未達があるあいだ Claude を終わらせない（1回戻すたびに1周）。`max_rounds`（初期値 3）に届いたら G1 に上げて止める。全部達成なら止めてよい。
- 終わり方は3つ（達成・人へ・予算切れ）。どれも `runs.jsonl` に1行。

### 最初の spec から足したこと（理由）
| 足したもの | 理由 |
|---|---|
| `checklist.py`（start・mark・reset・status） | 「証拠の無い項目は達成にしない」「検証役はスクリプトの後」を、文ではなくコードで守るため |
| `hooks/stop_guard.py`（Stop hook） | 周を数え、上限で G1 に上げる役（終了条件と予算上限）を、会話の外に置くため |
| `new_event.py`（init・adopt） | ひな形を写し、checklist を必ず未達から始めるため。途中のイベントの取り込みも同じ道具で |
| イベントごとの `budget.json` と `budget.last.json` | 前回との差を道具が見て、「計画の変更」を書くため |

## 3. Plan 内部設計・単体テスト条件
- `tests/recalc_budget/`：会場費 39,600・参加費 2,000・手数料 10% → 赤字にならない人数 22、40 人で +32,400。
- `tests/check_kit/`：【仮】が残る・G2 の記録あり → exit 1。

## 4. Tasks
- [x] ひな形（templates/）
- [x] new_event.py（init・adopt）
- [x] recalc_budget.py
- [x] checklist.py・check_kit.py
- [x] Stop hook（stop_guard.py）
- [x] reviewer-prompts.md
- [x] SKILL.md（plan-event）
- [ ] 人間ゲート：資料一式の形（Artifact・Luma）は 004 の adapter。いまは kit/ の Markdown まで
