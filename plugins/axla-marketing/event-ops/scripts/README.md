# event-ops の道具（spec 002：実行境界と承認ゲート）

送信・公開・支払いを「お願い」ではなく、道具で止めるための部品です。外部のライブラリは使いません（Python 3 の標準だけ）。

| 道具 | 7つ道具 | 何をするか |
|---|---|---|
| `../hooks/guard_send.py` | 実行境界（Sandbox）・承認ゲート（Human Gate） | Claude Code の PreToolUse hook。道具を呼ぶ直前に毎回動き、禁止の道具・承認の無い送信や公開・送った版の上書き・承認ファイルへの AI の書き込みを止める（exit 2）。止めたら `runs.jsonl` に1行書く |
| `approve.py` | 承認ゲート（Human Gate） | まとめ承認。**人が自分の端末で動かす**。表示された承認 ID を打ち込んだときだけ `approvals/A-NNN.json` を書く。端末の無い所（Claude Code の Bash・CI）では書かずに止まる |
| `check_outbound.py` | 検証器（Verifier） | 相手に出す中身に、社内の印・送り先ではない相手の名前やメールが無いかを見る。`names.local` が無ければ止まる（exit 2） |
| `check_pii.py` | 実行境界（Sandbox） | 使う側の git に、メール・電話番号・実名を入れないための検査。コミット前に動かす |
| `check_neutral.py` | 検証器（Verifier） | 公開リポの `event-ops/` に、特定の会社・人の情報が無いかを見る（CI） |

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
