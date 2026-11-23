# 005 · coordinate partners（相手とのやりとり・中間ループ）

> 会場・登壇者・スポンサーなどに資料一式を送り、返事とフィードバックで内側を呼び直す。返事は同じスレッドの下書きまで。送るのは人

**実装**: `event-ops/skills/coordinate-partners/SKILL.md`・`scripts/update_partners.py`・`scripts/freeze_kit.py`・`tests/test_partners.py`
**起源**: 001 の中間。最初の実例でいちばん時間を食った「会場との往復」。代表の想定「資料を投げまくってフィードバックで改善を回す」
**ステータス**: L2（実装・テスト済み。Human Judge のマージ待ち）

---

## 1. Specify
- 相手の種類（会場・登壇者・スポンサー・飲食・音響…）は config で足せる。種類ごとの雛形は使う人の EVENTS.md と templates/。
- 送る前に `freeze_kit.py` で、送る版を別の URL に凍結し、`sent/<相手番号>_<版>` に URL とハッシュを書く。送った URL は上書きしない（002 が止める）。
- 送り先の一覧と凍結した版で、まとめ承認を1つ作る（002。承認するのは人が端末で動かす approve.py）。下書きは承認のあとに作る（承認 ID は相手へのメールに入れない。hook が道具・宛先・版で引き当てる）。
- 返事を読み、**答える点・確かめる点・計画に効く点**に分ける。計画に効く点があれば plan-event を呼び直し、まだ送っていない下書きに「古い」の印を付けて止める。
- 電話・対面・チャットで決まったことは「offline」として人が入れる。
- `partners.csv`（番号・種類・状態・最後のやりとりの日・待っているもの。実名なし）は update_partners.py だけが書く。

受け入れ条件
- [ ] 返事の下書きが、相手のスレッドの中にあり、送信されていない（人間ゲート：メールのコネクタを使う試運転は、人がいるときに）
- [x] 料金が変わったあと、まだ送っていない下書きに【古い】が付き、そのままでは check_outbound が通さない（`test_drafts_become_stale_when_the_plan_changes`・`test_stale_draft_marker_fails`）。収支の表の作り直しは 003 の recalc_budget.py
- [x] partners.csv は番号だけ。名前で足そうとすると止まる（`test_rejects_names_instead_of_numbers`）
- [x] 同じ URL で中身が違う版は凍結できない。凍結の記録は spec 002 の hook がそのまま照合する（`test_refreezing_same_url_with_different_content_fails`・`test_frozen_record_is_honored_by_the_guard_hook`）
- [x] 会場の確定で G2 の記録が付く（`test_confirming_the_venue_records_g2`）。返事待ちの超過を数える（`test_overdue_replies_are_counted`）

## 2. Plan 外部設計
- `/axla-marketing:coordinate-partners`（スレッド ID・相手番号・「offline」のどれでも始められる）。

## 3. Plan 内部設計・単体テスト条件
- `tests/update_partners/`：送った→返事→確定 の状態の進み方と、規定日数を超えた返事待ちの検出。

## 4. Tasks
- [x] freeze_kit.py
- [x] update_partners.py（add・sent・replied・offline・confirmed・declined・overdue・draft・stale）
- [x] SKILL.md（coordinate-partners）
- [ ] 人間ゲート：メールのコネクタで、相手のスレッドへの返信の下書きを作る試運転
