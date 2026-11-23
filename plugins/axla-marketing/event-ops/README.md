# event-ops（Axla Marketing の機能）

**English** | [日本語](#日本語)

Runs an in-person event you host (tens of people, a rented venue) as a three-layer loop: build the launch kit (event page with eye-catch, overview, sponsor deck, venue layout) → send it to the venue and sponsors and improve it with their feedback, hold the event, thank and follow up with attendees → feed what you learned into the next event.

**Status: spec 002 (guard rails) and spec 003 (`/axla-marketing:plan-event`, the inner loop) are built** (a PreToolUse hook that stops sending, publishing and payments without a person's batch approval; see [scripts/README.md](scripts/README.md)). Start with [specs/001-define-event-loop.md](specs/001-define-event-loop.md). Skills (`/axla-marketing:plan-event`, `coordinate-partners`, `measure-event`, `review-event`) come after the specs are approved.

Sending, publishing, payments and contracts are always done by a person.

---

## 日本語

自分で会場を借りて開く数十人のイベントを、三層のループで回します。内側で告知（アイキャッチつき）・概要・スポンサー向け資料・会場レイアウトの一式を作り、中間で会場やスポンサーに送ってフィードバックで直し、開催し、来場者にお礼とフォローアップを送り、外側で学びを次のイベントの決まりに戻します。

**状態：spec 002（柵）と spec 003（`/axla-marketing:plan-event`、内側のループ）まで作った**（人のまとめ承認が無い送信・公開・支払いを止める PreToolUse hook。[scripts/README.md](scripts/README.md)）。 まず [specs/001-define-event-loop.md](specs/001-define-event-loop.md) を読んでください。スキル（`/axla-marketing:plan-event`・`coordinate-partners`・`measure-event`・`review-event`）は spec の承認のあとに作ります。

送信・公開・支払い・契約は、必ず人が行います。
