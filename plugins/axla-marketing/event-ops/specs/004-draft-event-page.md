# 004 · draft event page（告知の下書きとアイキャッチ・資料の形）

> 告知サービスにイベントを非公開の下書きとして作り、アイキャッチを付ける。資料一式を、使う人の選んだ形（Artifact など）で作る。公開は人が押す

**実装**: `adapters/events/{manual,luma}.md`・`adapters/docs/{manual,artifact}.md`・`scripts/make_eyecatch.py`
**起源**: 001 の内側。代表の想定「Luma にアイキャッチ込みで立ち上げ、Artifact で資料まで作る」。Luma の裏取り（公式 MCP `mcp.luma.com` でイベントの作成・更新・招待・一斉メッセージができる）
**ステータス**: L1（spec 起票・Human Judge 確認待ち）

---

## 1. Specify
- `~~events=luma`：公式 MCP でイベントを `visibility=private` で作る（名前・日時・場所・説明・定員・チケット）。カバー画像を上げて付ける。公開（public への変更）は「承認が要る」（002）。
- `~~events=manual`：告知サービスに貼る文面と画像のファイルを作るだけ。
- アイキャッチは文字だけの画像を `make_eyecatch.py` で作る（有料の画像生成は config で許したときだけ）。
- `~~docs=artifact`：資料一式を Artifact で作る。名前は `yyyymmdd_english-name_v1.0`。送るときは版ごとに別の URL に凍結する（005）。
- 資料に入れる数は plan.md から取り、社内の目的・目標の線は入れない（check_outbound.py が見る）。

受け入れ条件
- [ ] luma のとき、告知サービスに非公開のイベントがあり、カバー画像が付いている。公開されていない
- [ ] manual のとき、貼る文面と画像のファイルがそろう
- [ ] 資料の数が plan.md と一致し、check_outbound.py が exit 0

## 2. Plan 外部設計
- adapter は「何を呼び、何を返すか」を書いた Markdown。スキルは `~~events` のように種類名で書き、どの adapter かは config で選ぶ。

## 3. Plan 内部設計・単体テスト条件
- 公式 MCP で、カバー画像の `file_url` がそのまま使えるかを最初に試す（未確認）。

## 4. Tasks
- manual adapter → make_eyecatch.py → luma adapter（試運転）→ artifact adapter
