# 005 · coordinate partners（相手とのやりとり・中間ループ）

> 会場・登壇者・スポンサーなどに資料一式を送り、返事とフィードバックで内側を呼び直す。返事は同じスレッドの下書きまで。送るのは人

**実装**: `skills/coordinate-partners/SKILL.md`・`scripts/update_partners.py`・`scripts/freeze_kit.py`
**起源**: 001 の中間。最初の実例でいちばん時間を食った「会場との往復」。代表の想定「資料を投げまくってフィードバックで改善を回す」
**ステータス**: L1（spec 起票・Human Judge 確認待ち）

---

## 1. Specify
- 相手の種類（会場・登壇者・スポンサー・飲食・音響…）は config で足せる。種類ごとの雛形は使う人の EVENTS.md と templates/。
- 送る前に `freeze_kit.py` で、送る版を別の URL に凍結し、`sent/<相手番号>_<版>` に URL とハッシュを書く。送った URL は上書きしない（002 が止める）。
- 送り先の一覧と凍結した版で、まとめ承認を1つ作る（002）。下書きは承認 ID のラベル付きで作る。
- 返事を読み、**答える点・確かめる点・計画に効く点**に分ける。計画に効く点があれば plan-event を呼び直し、まだ送っていない下書きに「古い」の印を付けて止める。
- 電話・対面・チャットで決まったことは「offline」として人が入れる。
- `partners.csv`（番号・種類・状態・最後のやりとりの日・待っているもの。実名なし）は update_partners.py だけが書く。

受け入れ条件
- [ ] 返事の下書きが、相手のスレッドの中にあり、承認 ID のラベルが付き、送信されていない
- [ ] 料金が変わる返事のあと、plan.md の損益の表が作り直され、古い下書きに印が付く
- [ ] partners.csv と git の差分に実名・メールアドレス・相手の社名が 0件

## 2. Plan 外部設計
- `/axla-marketing:coordinate-partners`（スレッド ID・相手番号・「offline」のどれでも始められる）。

## 3. Plan 内部設計・単体テスト条件
- `tests/update_partners/`：送った→返事→確定 の状態の進み方と、規定日数を超えた返事待ちの検出。

## 4. Tasks
- freeze_kit.py → update_partners.py → SKILL.md
