---
name: plan-event
description: Use to start an in-person event you host, or to re-plan it when conditions change — purpose, targets sealed before the announcement, capacity, fee, budget and break-even, date options, and the launch kit (event page draft, eye-catch, overview, sponsor deck, venue layout), looped until every checklist item is met with evidence. Use when asked to plan or launch an event, when a venue or partner reply changes price, hours or headcount, or to take over an event already in progress. 日本語：自社で開くイベントを立ち上げるとき、条件が変わって計画し直すとき、途中のイベントを取り込むときに使う。目的・告知の前に封じる目標の線・定員・参加費・収支・日程の候補と、資料一式（告知の下書き・アイキャッチ・概要・スポンサー資料・会場レイアウト）を作り、checklist が証拠つきで全部達成になるまで回す。
---

# plan-event（内側のループ：一式をそろえる）

計画と資料一式を作り、**checklist が全部「達成」になるまで回す**。回すのも止めるのもコードが決める（Stop hook・checklist.py・check_kit.py）。送信・公開・支払いは人（承認ゲート）。

## 最初に読むもの
1. 決まり：`${CLAUDE_PLUGIN_ROOT}/event-ops/specs/001-define-event-loop.md`・`003-plan-event.md`
2. 道具：`${CLAUDE_PLUGIN_ROOT}/event-ops/scripts/README.md`
3. 検証役の指示文：`${CLAUDE_PLUGIN_ROOT}/event-ops/prompts/reviewer-prompts.md`
4. 使う側のデータ：`loop/marketing/event-ops/EVENTS.md`・`config.json`（全文を読む。書き換えない）。イベントがあれば `events/<ID>/event-log.md` の先頭

道具は `S="${CLAUDE_PLUGIN_ROOT}/event-ops/scripts"` として `python3 "$S/…"` で動かす。どれも使う側のリポのいちばん上で動かす。

## 0. どの入口か見分ける
- `events/` にそのイベントが無い → **新規**：`python3 "$S/new_event.py" init --id <yymmdd_英語の名前>`
- すでに送った資料や相手がいる途中のイベント → **取り込み**：`python3 "$S/new_event.py" adopt --id <ID> --partner PT-001:venue --sent PT-001:<URL>:<sha256>`
- イベントがあり、相手の返事などで条件が変わった → **呼び直し**：変わった前提だけ直す（下の 3）
- 使う側に `loop/marketing/event-ops/` が無く、新規でもないとき → 止めて、置き場所を人に聞く

## 1. 内側のループを始める
`python3 "$S/checklist.py" start --event loop/marketing/event-ops/events/<ID>`
→ ここから先、checklist に未達があるあいだ、Stop hook が終わらせない（周を数え、`max_rounds`＝初期値 3 で G1 に上げて止まる）。

## 2. 一式を作る（1周目）
1. `plan.md` を埋める。目的は社内向けと相手向けを分ける。目標の線は数と定義まで。人の判断が要る所は【G1】、会場が決まる前の数字は【仮】。実名は書かない（番号）。
   目標の線は `lines.json` に書き（metric と target）、**告知の公開の前に** `python3 "$S/judge_lines.py" seal --event <フォルダ>` で封じる（checklist の `lines` が達成になる。封じないと hook が公開を止める）。
2. `budget.json` を埋め、`python3 "$S/recalc_budget.py" --event <フォルダ>`。**収支は手で計算しない**。確かめていない前提は `unverified` に入れる（budget.md に「未確認」と出る）。
3. 資料一式を `kit/` に作る。形は config の `adapters`（`${CLAUDE_PLUGIN_ROOT}/event-ops/adapters/README.md`）。
   - 告知：`event.json` を埋めて `python3 "$S/event_page.py" --event <フォルダ>`（定員・参加費が budget.json と違えば止まる。visibility はいつも private）。アイキャッチは `python3 "$S/make_eyecatch.py" --title … --date … --out <フォルダ>/kit/eyecatch.png`
   - 資料（概要・スポンサー向け・会場レイアウト）：manual なら Markdown、artifact なら Artifact（名前は yyyymmdd_english-name_v1.0）
4. `python3 "$S/check_outbound.py" --names loop/marketing/event-ops/names.local --to <送る相手の番号> kit/*` が exit 0 になったら、その出力を `evidence/outbound.md` に保存して `checklist.py mark --item outbound`。
5. 書いた項目ごとに `checklist.py mark --item <ID> --evidence <パス>`。証拠の無い項目は達成にならない。
6. 検証役3体を並列に動かす（reviewer-prompts.md）。記録を `reviews/round-<周>-<役>.md` に保存し、`mark --item review_money|review_safety|review_outbound`。致命的が 0 でなければ達成にならない。
7. `python3 "$S/check_kit.py" --event <フォルダ>` が exit 0 → 内側は完了。終えてよい。

未達が残ったまま終えようとすると、Stop hook が「周 n/3：未達 …」と返して戻す。そのときは未達の項目だけ直す。

## 3. 呼び直し（条件が変わったとき）
- 料金・時間・人数 → `budget.json` を直して `recalc_budget.py --event`。収支が変わると、記録の「計画の変更」に1行入り、収支に関わる項目が自動で未達に戻る。
- 日程 → `checklist.py reset --event <フォルダ> --because date`。会場 → `--because venue`。
- そのあと `checklist.py start` で内側をもう一度回す。

## 4. 終わり方は3つ
- **達成**：check_kit.py が exit 0。event-log の先頭（いまの状態と次の一手）を更新し、「次は coordinate-partners で送る（まとめ承認が要る）」と人に3行で知らせる。
- **人へ（G1）**：3周で終わらない／事業の判断が要る。Stop hook が event-log の「開いている人の判断」に書く。人に3行で知らせて止まる。
- **予算切れ**：上の G1 と同じ扱い。

## 守ること
- 告知の公開・メールの送信・資料の共有・支払いはしない（hook が止める。人のまとめ承認と G2）。
- 封じた目標の線は、告知の公開のあとは書き換えない。変えたくなったら G1。
- 実名・連絡先・相手の社名は git に入るファイルに書かない（`check_pii.py` で確かめる）。
