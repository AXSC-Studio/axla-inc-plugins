# 003 · plan event（立ち上げ・内側ループ）

> 目的・目標の線・定員・参加費・収支・日程の候補と、資料一式を作り、checklist が全部「達成」になるまで直す。すでに動いているイベントは途中から取り込む

**実装**: `skills/plan-event/SKILL.md`・`scripts/recalc_budget.py`・`scripts/check_kit.py`・`prompts/reviewer-prompts.md`・`templates/`（plan.md・event-log.md・checklist.json・EVENTS.md・config.json）
**起源**: 001 の内側。最初の実例で時間を食った「収支と日程の計算し直し」
**ステータス**: L1（spec 起票・Human Judge 確認待ち）

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
- [ ] checklist.json の全項目が「未達」から始まり、達成の項目にはすべて証拠のパスがある
- [ ] 料金を変えて呼び直すと、損益の表が作り直され、event-log に「計画の変更」が1行増える
- [ ] 検証役3体は、3つのスクリプトが全部 exit 0 になった後にだけ動く
- [ ] 3周で致命的が 0件にならなければ、G1 に上げて止まる

## 2. Plan 外部設計
- `/axla-marketing:plan-event`（新規・呼び直し・adopt を自分で見分ける）。

## 3. Plan 内部設計・単体テスト条件
- `tests/recalc_budget/`：会場費 39,600・参加費 2,000・手数料 10% → 赤字にならない人数 22、40 人で +32,400。
- `tests/check_kit/`：【仮】が残る・G2 の記録あり → exit 1。

## 4. Tasks
- ひな形 → recalc_budget.py → check_kit.py → reviewer-prompts.md → SKILL.md（adopt を最初に）
