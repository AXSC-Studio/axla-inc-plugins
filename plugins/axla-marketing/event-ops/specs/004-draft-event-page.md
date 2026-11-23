# 004 · draft event page（告知の下書きとアイキャッチ・資料の形）

> 告知サービスにイベントを非公開の下書きとして作り、アイキャッチを付ける。資料一式を、使う人の選んだ形（Artifact など）で作る。公開は人が押す

**実装**: `event-ops/adapters/`（events：manual・luma／docs：manual・artifact）・`scripts/event_page.py`・`scripts/make_eyecatch.py`・`templates/event.json`・`tests/test_event_page.py`
**起源**: 001 の内側。代表の想定「Luma にアイキャッチ込みで立ち上げ、Artifact で資料まで作る」。Luma の裏取り（公式 MCP `mcp.luma.com` でイベントの作成・更新・招待・一斉メッセージができる）
**ステータス**: L2（manual と道具は実装・テスト済み。luma は人間ゲートの試運転待ち）

---

## 1. Specify
- `~~events=luma`：公式 MCP でイベントを `visibility=private` で作る（名前・日時・場所・説明・定員・チケット）。カバー画像を上げて付ける。公開（public への変更）は「承認が要る」（002）。
- `~~events=manual`：告知サービスに貼る文面と画像のファイルを作るだけ。
- アイキャッチは文字だけの画像を `make_eyecatch.py` で作る（有料の画像生成は config で許したときだけ）。
- `~~docs=artifact`：資料一式を Artifact で作る。名前は `yyyymmdd_english-name_v1.0`。送るときは版ごとに別の URL に凍結する（005）。
- 資料に入れる数は plan.md から取り、社内の目的・目標の線は入れない（check_outbound.py が見る）。

受け入れ条件
- [ ] luma のとき、告知サービスに非公開のイベントがあり、カバー画像が付いている。公開されていない（人間ゲート：Luma の公式 MCP のログインが要るので、無人では試していない）
- [x] manual のとき、貼る文面と画像のファイルがそろう（`test_builds_markdown_and_payload`・`test_makes_png_of_the_configured_size`）
- [x] 告知の定員・参加費が budget.json と一致しなければ止まる（`test_capacity_mismatch_with_budget_fails`・`test_fee_mismatch_with_budget_fails`）。公開の設定はいつも private（`test_visibility_is_always_private`）

## 2. Plan 外部設計
- adapter は「何を呼び、何を返すか」を書いた Markdown。スキルは `~~events` のように種類名で書き、どの adapter かは config で選ぶ。

## 3. Plan 内部設計・単体テスト条件
- 公式 MCP で、カバー画像の `file_url` がそのまま使えるかを最初に試す（未確認）。

## 4. Tasks
- [x] manual adapter・event_page.py・make_eyecatch.py
- [x] luma adapter・artifact adapter の手順書
- [ ] 人間ゲート：Luma の公式 MCP を足してログインし、非公開のイベントを1件作る試運転（カバー画像の上げ方・道具の名前を確かめ、hook の分け方を config に足す）
