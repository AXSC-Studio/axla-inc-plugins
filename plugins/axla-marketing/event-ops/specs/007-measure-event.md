# 007 · measure event（当日・撤収・お礼）

> 当日の段取り表を作り、終わったら件数と撤収の確認を記録し、来場者にお礼とフォローアップを送る（下書きまで）

**実装**: `event-ops/skills/measure-event/SKILL.md`・`scripts/count_roster.py`・`scripts/close_event.py`・`templates/run-sheet.md`・`templates/thanks.md`・`tests/test_measure.py`
**起源**: 001 の中間の終わり。代表の想定「イベントが完全に終わったらお客さんにお礼とフォローアップ」
**ステータス**: L2（実装・テスト済み。Human Judge のマージ待ち）

---

## 1. Specify
- 段取り表：搬入〜撤収の時刻・係・確認の表（撤収の確認の項目を含む）。plan.md から作る。
- 件数：名簿の CSV（または `~~metrics`）を `count_roster.py` で数え、申し込み・来場・同意・収支の実績を件数だけ register.csv に書き、名簿は捨てる。
- お礼とフォローアップ：来場者（checked_in）だけに送る下書きを作る。luma のときは一斉メッセージの下書き。送る前に、人が checked_in の件数と受付の実数を見比べる。送信は「承認が要る」（002）。
- 後日の面談などを希望した人の連絡先は `~~crm` だけに置く（登録のときの質問で取る）。
- 中間の達成＝撤収の確認・精算・お礼の送信の3つがそろったとき。そろったら「終了」の印を立てる（外側の起動）。

受け入れ条件
- [x] register.csv に件数だけがあり、名前・連絡先が無い。`--delete` で名簿を消す（`test_counts_only`・`test_delete_removes_the_roster`）
- [x] お礼の下書きの送り先が checked_in だけになっている（`test_thanks_draft_goes_to_checked_in_only`）
- [x] 3つがそろうまで「終了」が立たない。撤収の確認は段取り表の箱が全部 [x] のときだけ（`test_not_closed_until_three_conditions`・`test_teardown_needs_every_box_checked`・`test_closes_and_marks_outer_trigger`）

## 4. Tasks
- [x] run-sheet・thanks のひな形（new_event.py が写す）
- [x] count_roster.py
- [x] close_event.py（status・teardown・settle・thanks-draft・thanks-sent）
- [x] SKILL.md（measure-event）
- [ ] 人間ゲート：告知サービスの名簿の書き出しの列の名前を、最初の本番で確かめる（違えば config.json の roster_columns）
