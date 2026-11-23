# ~~events = luma（公式 MCP）

**つなぐ（人間ゲート・1回だけ）**：人が Claude Code に Luma の公式 MCP を足し、Luma のアカウントでログインする。

```bash
claude mcp add --transport http luma https://mcp.luma.com
```

**作る**
1. `python3 scripts/event_page.py --event <フォルダ>` で `kit/event_page.json` を作る（visibility はいつも private）
2. `python3 scripts/make_eyecatch.py … --out kit/eyecatch.png`
3. Luma の MCP のイベント作成の道具に、`event_page.json` の値（name・start_at・end_at・timezone・description_md・max_capacity・visibility=private）を渡す
4. カバー画像に `kit/eyecatch.png` を上げて付ける
5. 返ってきたイベントの URL を `kit/event_page.url` に書き、`checklist.py mark --item event_page --evidence kit/event_page.url`

**公開**：visibility を public にする更新・一斉メッセージ・招待は、spec 002 の hook が止める。人のまとめ承認（`approve.py new … --tools <その道具の名前>`）のあとだけ通る。

**未確認（最初の試運転で確かめる）**
- 公式 MCP でカバー画像を上げる手順と、上げた画像の URL をそのまま `cover_url` に使えるか
- 有料チケットの作成に Stripe の接続が要るか（要るなら、チケットは人が付ける）
- Luma の道具の名前（hook の分け方に合わない名前があれば `config.json` の `send_tools`・`allow_tools` に足す）
