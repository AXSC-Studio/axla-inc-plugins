# ~~events = manual（告知サービスに人が貼る）

1. `python3 scripts/event_page.py --event <フォルダ>` で `kit/event_page.md` を作る（定員・参加費が budget.json と食い違えば止まる）
2. `python3 scripts/make_eyecatch.py --title … --date … --out kit/eyecatch.png` でアイキャッチを作る
3. 人が告知サービスに、文面と画像を**非公開（下書き）**で貼る
4. 貼った下書きの URL を `kit/event_page.url` に1行で書き、`checklist.py mark --item event_page --evidence kit/event_page.url`

公開は、まとめ承認（`approve.py`）のあとに人が押す。
