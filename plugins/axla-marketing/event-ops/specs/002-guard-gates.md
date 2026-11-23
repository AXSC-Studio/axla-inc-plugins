# 002 · guard gates（実行境界と承認ゲート）

> 送信・公開・支払いを「お願い」ではなく実行境界（Sandbox）で止める。人が1回だけ承認した「凍結した版＋宛先」の外には、何も出ていかないようにする。最初に作る

**実装**: `event-ops/hooks/hooks.json`（plugin.json の hooks で読み込む）・`event-ops/hooks/guard_send.py`・`scripts/approve.py`・`scripts/check_outbound.py`・`scripts/check_neutral.sh`（CI）・`scripts/check_pii.py`
**起源**: 001 の「送信」ゲート。世界のベンチマーク（データを変える道具を「禁止／承認が要る／常に許可」で分ける形）
**ステータス**: L1（spec 起票・Human Judge 確認待ち）

---

## 1. Specify
- 道具を3つに分ける：**禁止**（支払い・契約・イベントの中止）／**承認が要る**（メールの送信、告知の公開、一斉メッセージ、招待、資料の共有設定）／**常に許可**（読む道具、下書きを作る道具）。分け方は `config.json` の `send_tools`・`pay_tools` で上書きできる。
- 「承認が要る」道具は、有効な承認 ID がなければ PreToolUse hook が止める（exit 2）。宣言していない `mcp__*send*`・`*blast*`・`*publish*` も止める。
- まとめ承認は `approvals/A-NNN.json` に、凍結した版の URL・版のハッシュ・宛先の一覧・承認した人と日時を持つ。小さな文面の修正は差分として追記し、朝の知らせに出す（承認はやり直さない）。宛先が増える・版が変わるときは新しい承認にする。
- `check_outbound.py`：相手に出すものに、社内の印（【要確認】など）・ほかの相手の名前・社内の目的が混ざっていれば exit 1。照合の元は git の外の `names.local`。無ければ exit 2。

受け入れ条件
- [ ] 承認 ID の無い送信・公開の道具の呼び出しが、hook で止まる
- [ ] 承認にない宛先、ハッシュの違う版への送信が止まる
- [ ] 送った版の URL への上書きの公開が止まる
- [ ] `check-neutral` が、`event-ops/` に特定の会社・人の名前が入った PR で落ちる

## 2. Plan 外部設計
- `scripts/approve.py new --kit <URL> --to <番号の一覧>` → 人に要点を見せ、人が `--yes` で承認したときだけ承認ファイルを書く。
- hook は承認ファイルを読むだけ。承認ファイルを書けるのは approve.py だけ。

## 3. Plan 内部設計・単体テスト条件
- `tests/guard_send/`：承認あり・なし・宛先違い・ハッシュ違い・未宣言の送信道具、の5例。

## 4. Tasks
- hooks.json と guard_send.py → approve.py → check_outbound.py → CI（check-neutral）
