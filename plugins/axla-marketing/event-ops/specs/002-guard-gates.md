# 002 · guard gates（実行境界と承認ゲート）

> 送信・公開・支払いを「お願い」ではなく実行境界（Sandbox）で止める。人が1回だけ承認した「凍結した版＋宛先」の外には、何も出ていかないようにする。最初に作る

**実装**: `event-ops/hooks/hooks.json`（plugin.json の `hooks` で読み込む）・`event-ops/hooks/guard_send.py`・`event-ops/scripts/approve.py`・`check_outbound.py`・`check_pii.py`・`check_neutral.py`（CI：`.github/workflows/event-ops.yml`）・`event-ops/tests/`
**起源**: 001 の「送信」ゲート。世界のベンチマーク（データを変える道具を「禁止／承認が要る／常に許可」で分ける形）
**ステータス**: L2（実装・テスト済み。Human Judge のマージ待ち）

---

## 1. Specify
- 道具を3つに分ける：**禁止**（支払い・契約・イベントの中止）／**承認が要る**（メールの送信・返信・転送、告知の公開、一斉メッセージ、招待、共有）／**常に許可**（読む道具、下書きを作る道具）。分け方は `config.json` の `send_tools`・`pay_tools`・`allow_tools` で足せる。
- 「承認が要る」道具は、有効なまとめ承認が無ければ PreToolUse hook が止める（exit 2）。宣言していない `*send*`・`*blast*`・`*publish*`・`*invite*`・`*share*` も止める。名前に出ない公開（`visibility` を `public` にする更新）も止める。`get_`・`list_`・`search_` などで始まる読む道具は通す。
- まとめ承認は `approvals/A-NNN.json` に、凍結した版の URL・版のハッシュ・宛先（相手の番号）・道具・承認した人と日時・期限を持つ。小さな文面の修正は `amendments` に追記し、朝の知らせに出す（承認はやり直さない）。宛先が増える・版が変わるときは新しい承認にする。
- 承認ファイルを書けるのは、**人が自分の端末で動かす** `approve.py` だけ。AI の Write・Edit・書き込みのコマンドは hook が止める。
- 送った版の URL への上書きの公開（Artifact の publish）は hook が止める。
- `check_outbound.py`：相手に出すものに、社内の印（【要確認】など）・送り先ではない相手の名前やメールが混ざっていれば exit 1。照合の元は git の外の `names.local`。無ければ exit 2。
- 止めたときは `runs.jsonl` に1行書く（観測記録。実名・宛先は書かない）。
- 使う側に `loop/marketing/event-ops/` が無いリポでは、hook は何もしない（ほかの仕事を邪魔しない）。

受け入れ条件
- [x] 承認の無い送信・公開の道具の呼び出しが、hook で止まる（`test_send_without_approval_is_blocked` ほか）
- [x] 承認にない宛先、ハッシュの違う版への送信が止まる（`test_send_to_unapproved_recipient_is_blocked`・`test_send_with_wrong_kit_hash_is_blocked`）
- [x] 送った版の URL への上書きの公開が止まる（`test_republishing_a_sent_kit_url_is_blocked`）
- [x] `check_neutral.py` が、`event-ops/` に特定の会社・人の情報が入ると落ちる（`CheckNeutralTest`）
- [x] 本物の Claude Code（`--plugin-dir`）で、承認ファイルへの Write が止まり、`runs.jsonl` に1行残る（2026-11-23 に手で確認）

## 2. Plan 外部設計
- `approve.py new --event <フォルダ> --kit <URL> --sha256 <ハッシュ> --to PT-001,PT-002 --tools send_message` → 端末に要点を出し、人が承認 ID を打ち込んだときだけ承認ファイルを書く。`show`（一覧）・`amend`（小さな直しの追記）。
- hook は承認ファイルを読むだけ。

### 最初の spec から変えたこと（理由）
| 最初 | 実装 | 理由 |
|---|---|---|
| 人が `--yes` で承認する | 端末（/dev/tty）で承認 ID を打ち込む。`--yes` は無い | `--yes` は AI も付けられる。端末の入力は、Claude Code の Bash や CI からは届かない |
| 送信の呼び出しに承認 ID を書く | 道具・宛先・版の3つで承認を自動で引き当て、使った承認 ID を `runs.jsonl` に書く | メールの本文に社内の ID を入れたくない。Gmail の送信の道具にはラベルの欄も無い |
| `check_neutral.sh` | `check_neutral.py` | ほかの道具とそろえ、テストで検査するため |

## 3. Plan 内部設計・単体テスト条件
- `tests/test_guard_send.py`：承認あり・なし・宛先違い・ハッシュ違い・期限切れ・承認にない道具・未宣言の送信の道具・visibility の公開・読む道具は通す・支払いは承認があっても止める・送った版の上書き・承認ファイルへの書き込み・記録・event-ops の無いリポ（17件）
- `tests/test_scripts.py`：check_outbound・check_pii・check_neutral・approve（14件）
- テストの見本の会社名や電話番号は、文字列をつなげて作る（check_neutral が自分のテストに引っかからないように）

## 4. Tasks
- [x] hooks.json と guard_send.py
- [x] approve.py
- [x] check_outbound.py・check_pii.py
- [x] CI（check_neutral・テスト）
- [ ] 人間ゲート：Secrets に `NEUTRAL_DENYLIST`（隠したい会社名・人名を1行1語）を入れる。無くても、形の検査とテストは動く
