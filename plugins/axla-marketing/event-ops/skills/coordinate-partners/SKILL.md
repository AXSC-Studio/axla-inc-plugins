---
name: coordinate-partners
description: Use to handle the back-and-forth with the people who make an event happen — venue, speakers, sponsors, catering, sound. Freezes the version you send, prepares a batch approval for a person, drafts replies in the same email thread (never sends), records each partner's status by number, re-plans when a reply changes price, hours or headcount, and marks old drafts stale. Use when a partner replies, when the reply watcher sends a thread ID, or when asked to send the kit to venues and sponsors. 日本語：会場・登壇者・スポンサーなど、イベントの相手とのやりとり（中間ループ）に使う。送る版を凍結し、人のまとめ承認を用意し、同じスレッドに返事の下書きを作り（送らない）、相手の状態を番号で台帳に残す。料金・時間・人数が変わる返事なら計画を呼び直し、古い下書きに印を付けて止める。
---

# coordinate-partners（中間ループ：送る・返事・直す）

送るのは人。ループは「凍結した版＋宛先」をまとめ承認に出すところと、返事の下書きまで。送信・公開・共有は spec 002 の hook が止める。

## 最初に読むもの
1. 決まり：`${CLAUDE_PLUGIN_ROOT}/event-ops/specs/005-coordinate-partners.md`（全体は 001）
2. 道具：`${CLAUDE_PLUGIN_ROOT}/event-ops/scripts/README.md`
3. 使う側：`loop/marketing/event-ops/EVENTS.md`（相手の種類ごとの雛形）・`config.json`・`partners.csv`、そのイベントの `event-log.md` の先頭

道具は `S="${CLAUDE_PLUGIN_ROOT}/event-ops/scripts"`、`E=loop/marketing/event-ops/events/<ID>` として動かす。

## A. 一式を送る（なげる）
1. 内側が終わっているか：`python3 "$S/check_kit.py" --event $E` が exit 0。でなければ plan-event に戻る
2. 相手を台帳に：`python3 "$S/update_partners.py" add --partner PT-002 --kind sponsor --event $E`（名前は names.local にだけ）
3. 送る版を凍結：`python3 "$S/freeze_kit.py" --event $E --partner PT-002 --url <資料の URL> --file <その版の中身> --version v1.0` → 出たハッシュを控える
4. 相手ごとの送る文面を下書きし、`python3 "$S/check_outbound.py" --names loop/marketing/event-ops/names.local --to PT-002 <下書き>` が exit 0 になるまで直す。`update_partners.py draft --partner PT-002 --file <下書き> --event $E` で登録
5. **人に、まとめ承認を頼んで止まる**。人が自分の端末で：
   `python3 "$S/approve.py" new --event $E --kit <URL> --sha256 <ハッシュ> --to PT-002,PT-003 --tools <送る道具の名前>`
6. 承認のあと、メールの下書き（同じスレッドへの返信）を作る。送るのは人。送ったら `update_partners.py sent --partner PT-002 --event $E`（gmail の見張りがあれば自動）

## B. 返事が来た
1. 返事を読み、**答える点・確かめる点・計画に効く点**に分ける。返事が別のスレッドで来ることがあるので、相手のドメインと日時でも探す
2. `update_partners.py replied --partner PT-002 --event $E`（電話や対面で決まったことは `offline --note`）
3. 計画に効く点（料金・時間・人数・日程）があれば：`budget.json`・`event.json` を直し `recalc_budget.py --event $E`。`update_partners.py stale --event $E` で、まだ送っていない下書きに【古い】が付く（【古い】のままでは check_outbound が通さない）。plan-event で内側を回し直す
4. 返事の下書きを作り、A の 4〜6 と同じ道で送る
5. 会場が決まったら `update_partners.py confirmed --partner PT-001 --event $E`（G2 の記録。会場の申し込み・支払いは人）

## C. 毎朝
`python3 "$S/update_partners.py" overdue --days <config の reply_wait_days> --event $E` が exit 1 なら、返事待ちの相手を人に知らせる（催促の下書きまで）。

## 守ること
- 送信・公開・共有・支払いはしない（hook が止める）。金額の相談（値引き・条件の交換）を入れるかは G1
- 相手は番号で書く。実名・メール・社名は git に入るファイルに書かない
- 凍結した版は直さない。直すなら版を上げて新しい URL で（hook が上書きを止める）
