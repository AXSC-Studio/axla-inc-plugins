# event-ops の道具（spec 002：実行境界と承認ゲート／spec 003：内側のループ）

送信・公開・支払いを「お願い」ではなく、道具で止めるための部品です。外部のライブラリは使いません（Python 3 の標準だけ）。

| 道具 | 7つ道具 | 何をするか |
|---|---|---|
| `../hooks/guard_send.py` | 実行境界（Sandbox）・承認ゲート（Human Gate） | Claude Code の PreToolUse hook。道具を呼ぶ直前に毎回動き、禁止の道具・承認の無い送信や公開・送った版の上書き・承認ファイルへの AI の書き込みを止める（exit 2）。止めたら `runs.jsonl` に1行書く |
| `approve.py` | 承認ゲート（Human Gate） | まとめ承認。**人が自分の端末で動かす**。表示された承認 ID を打ち込んだときだけ `approvals/A-NNN.json` を書く。端末の無い所（Claude Code の Bash・CI）では書かずに止まる |
| `check_outbound.py` | 検証器（Verifier） | 相手に出す中身に、社内の印・送り先ではない相手の名前やメールが無いかを見る。`names.local` が無ければ止まる（exit 2） |
| `check_pii.py` | 実行境界（Sandbox） | 使う側の git に、メール・電話番号・実名を入れないための検査。コミット前に動かす |
| `check_neutral.py` | 検証器（Verifier） | 公開リポの `event-ops/` に、特定の会社・人の情報が無いかを見る（CI） |
| `new_event.py` | 起動トリガー（Trigger） | イベントのフォルダをひな形から作る（init）。途中のイベントを取り込む（adopt）。checklist は必ず未達から |
| `recalc_budget.py` | 検証器（Verifier） | 収支を計算し直す。前回から変わったら「計画の変更」に1行書き、収支に関わる項目を未達に戻す |
| `checklist.py` | 状態ストア（State Store） | 内側の台帳。証拠の無い項目・致命的が残る検証役の項目は達成にできない。検証役はスクリプトの後 |
| `check_kit.py` | 検証器（Verifier） | 全項目が証拠つきで達成なら exit 0。会場の確定（G2）のあとに【仮】が残れば exit 1 |
| `../hooks/stop_guard.py` | 終了条件（Exit Criteria）・予算上限（Budget Cap） | Stop hook。内側のループの途中は終わらせない。上限の周で G1 に上げて止める |
| `event_page.py` | 検証器（Verifier） | event.json から告知の文面（Markdown）と告知サービスに渡す中身（JSON）を作る。visibility はいつも private。定員・参加費が budget.json と違えば止まる |
| `make_eyecatch.py` | — | 文字だけのアイキャッチ（外の API を呼ばない。Pillow が要る） |
| `freeze_kit.py` | 状態ストア（State Store） | 送る版を凍結（URL と中身のハッシュ）。同じ URL で中身が違えば止める。ハッシュを approve.py に渡す |
| `update_partners.py` | 状態ストア・検証器 | 相手の台帳（番号だけ）を進める。会場の確定で G2 を記録。返事待ちの超過・古い下書き（【古い】）を見つける |
| `apps-script/watch_partner_mail.gs` | 起動トリガー（Trigger） | 相手の返事と、相手のドメイン宛の送信済みを拾い、種類とスレッド ID だけをルーティンへ送る（1分ごと） |
| `match_partner.py` | — | アドレスを相手の番号に手元で引き当てる（names.local は外に出さない） |
| `count_roster.py` | 検証器（Verifier） | 名簿から申し込み・来場・同意の件数だけを台帳に入れる。`--delete` で名簿を消す |
| `close_event.py` | 終了条件（Exit Criteria）・起動トリガー | 撤収の確認・精算・お礼の送信の3つがそろったらイベントを閉じ、外側を起こす。お礼の下書きは来場者だけ宛て |
| `judge_lines.py` | 検証器（Verifier） | seal：目標の線のハッシュを register.csv に刻む（告知の公開の前。封じていないと hook が公開を止める）。judge：封じた線と結果を照らし、人の判断の数を前回と比べ、2回出た失敗を決まりの案にする |
| `eventops_lib.py` | — | 上の道具が共有する部品（置き場・runs.jsonl・checklist） |

## 道具の分け方

| 分け | 例 | hook の扱い |
|---|---|---|
| 禁止 | 支払い・課金・契約・イベントの中止 | いつも止める。承認があっても止める（G2 は人） |
| 承認が要る | メールの送信・返信・転送、告知の公開（visibility を public にする更新も）、一斉メッセージ、招待、共有 | 有効なまとめ承認が無ければ止める |
| 常に許可 | 読む道具（get・list・search…で始まる）、下書きを作る道具 | 通す |

名前で分けられない道具は、使う側の `config.json` に書いて足します。

```json
{ "send_tools": ["mcp__example__deliver"], "pay_tools": ["mcp__example__settle"], "allow_tools": ["mcp__example__share_preview"] }
```

## まとめ承認の通り方

hook は、送信の道具の呼び出しを次の順に確かめ、1つでも合う承認があれば通します。

1. 承認の `tools` に、その道具の名前がある
2. 承認の期限（既定 7日）が切れていない
3. 呼び出しの中のメールアドレスが、すべて承認の `to`（相手の番号）に入っている。番号とメールの対応は `names.local` で引く
4. 呼び出しの中に送った版の URL があれば、その版の凍結の記録（`sent/*.json` の sha256）と、承認のハッシュが同じ

## 使う側に置くもの（git に入れないもの）

```
loop/marketing/event-ops/
├── names.local          … 番号<TAB>名前<TAB>メール。git に入れない
├── config.json          … 道具の分け方の足し（任意）
├── runs.jsonl           … 1周1行の記録（hook が書く。実名なし）
└── events/<ID>/         … git に入れない
    ├── approvals/A-NNN.json   … approve.py だけが書く
    └── sent/<相手>_<版>.json  … 凍結した版の URL とハッシュ（spec 005 の freeze_kit.py が書く）
```

使う側の `.gitignore` に足すもの：

```
loop/marketing/event-ops/names.local
loop/marketing/event-ops/events/
```

## テスト

```bash
python3 -m unittest discover -s plugins/axla-marketing/event-ops/tests -v
```
