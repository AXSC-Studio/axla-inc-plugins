# Axla Legal (`axla-legal`)

**English** | [日本語](#日本語)

A Claude Code plugin that runs a contract you received (starting with NDAs) from intake, through your own redline and the back-and-forth with the other party, up to signature.

## What it does
- Puts your proposed changes into the other party's .docx as tracked changes (insertions and deletions), with a Word comment explaining each change
- Checks the redline before sending, using internal reviewers with four viewpoints: your lawyer, the other party's legal team, formatting, and generative-AI clauses
- Builds the clean copy to send and the reply email body with tools, not by hand
- Records each contract's status, version and number of round trips in a ledger (`register.csv`)

## Requirements
- **Claude Code** (terminal, desktop or IDE). It does not run in a claude.ai chat: the tools run locally.
- **Python 3.13** (standard library only; no virtual environment or extra packages) and **git**.
- **Google Drive and Gmail connectors** in Claude, for the original, the internal Google Doc and reply drafts.
- Built for **Japanese-language contracts (.docx) and Japanese business practice**. Unlike a general legal-review plugin, it edits the .docx itself and enforces the pre-send checks with hooks.

## Install
Run in your terminal. `--scope user` makes it available in every project on this Mac.

```bash
claude plugin marketplace add AXSC-Studio/axla-inc-plugins
claude plugin install axla-legal@axla-inc-plugins --scope user
```

To share it with your team through one repository instead, run the install line there with `--scope project` (it is written to that repository's settings, which you commit).

## Data and network
| Where it goes | What | Why |
|---|---|---|
| The Claude model you use | The text Claude reads (contract, your rules, records) | As in any Claude Code session |
| Your Google Drive (connector) | Reads the original; creates the internal Google Doc | Review by your CEO or legal owner |
| Your Gmail (connector) | Creates and reads reply drafts | Sending is always done by a person |
| Google Drive API (optional) | `resolve_comments.py`, with your own `gcloud` token | Only when fixing an existing Google Doc |
| Your Claude routine (optional, experimental) | `notify_reply.gs` sends a Gmail thread ID only | Wakes a read-only watcher when a reply arrives ([routines/reply-watcher.md](routines/reply-watcher.md)). Uses a beta API and may stop working without notice |

Hooks run locally. Nothing is sent to Axla Inc. Details: [PRIVACY.md](PRIVACY.md).

## Data handling
- Per-contract records stay in your repository under `loop/legal/contracts/<id>/`, which must be git-ignored (the tools stop if it is not). The ledger has no counterparty names.
- Tools such as `view.py` print contract text, so it appears in your session transcript. Keep sessions private.
- Delete the work folder after each round (`rm -rf "$W"`), and the record folder when the contract no longer needs it.

## Troubleshooting
- **"loop/legal/contracts/ is not git-ignored"**: add the line from `templates/gitignore.txt` to your `.gitignore`.
- **"No author name"**: copy `templates/config.json` to `loop/legal/config.json` and fill in your values.
- **A hook blocked an action**: read the reason; it names the missing check (clean copy, draft check, …). Run that step instead of working around it.
- **`${CLAUDE_PLUGIN_ROOT}` is empty in a shell**: it is only expanded inside skills; use the absolute path shown by the skill.
- **The draft check never runs**: read the draft with `get_draft` and `messageFormat=RAW`; the hook checks it.

## How to use
1. Install (above)
2. In the repository where you will use it, create `loop/legal/` and put your own rules `LEGAL.md` and your ledger `register.csv` there (columns are in [docs/register.md](docs/register.md))
3. Add one line to that repository's `.gitignore`: `loop/legal/contracts/` (the tools stop if it is missing)
4. Type `/axla-legal:loop` (or ask "Please review this contract"). The entry reads where each contract stands and runs only the next step: `intake` → `redline-contract` → `review` → `gdoc` → `send` → `learn`. It stops and tells you when it is waiting for a person (final OK, sending, signing)

Contract text and per-contract records never go into this plugin or into git. Sending, signing and any decision outside your rules are always done by a person.

## Try it in 5 minutes (no Google account needed)
`examples/` has a fictional NDA between two made-up companies, a sample redline (`Redline Data.json`) and a sample reviewer output. In a terminal, with `T` set to this plugin's `scripts` folder and `E` to its `examples` folder:

```bash
W=$(mktemp -d)
python3 -I -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$E/example-nda.docx" "$W/work"
python3 -I "$T/redline.py" "$W/work" "$E/Redline Data.json"        # tracked changes
python3 -I "$T/view.py" "$W/work" changed                           # see what changed
python3 -I "$T/check_refs.py" "$W/work" --out "$W/review-refs.md"   # clause references
cp "$E/review-sample.md" "$W/review-a.md"
python3 -I "$T/count_findings.py" "$W"/review-*.md                  # pass or fail, counted by a tool
python3 -I "$T/make_clean.py" "$W/work" --out "$W/clean.docx"       # the clean copy to send
python3 -I "$T/make_reply.py" "$E/Redline Data.json" --out-text "$W/reply.txt" --out-html "$W/reply.html"
```

Templates for your own repository are in `templates/` (`LEGAL.md`, `register.csv`, `config.json` with your company name and the author name for tracked changes, and the `.gitignore` line). Nothing in the plugin is tied to one company.

## Example prompts
- "An NDA arrived from a new partner. `/axla-legal:loop`" — starts intake, then the redline and review.
- "The other party replied to our NDA redline. What's next? `/axla-legal:loop 261123_NDA_1`" — reads their version and runs the next round.
- "I gave the final OK. Prepare the reply draft and check it before I send." — builds the clean copy and reply, then runs the pre-send check (sending stays with you).

## Guardrails (hooks)
The plugin ships hooks that stop, instead of just asking: sending mail to a contract counterparty, creating a reply draft before the clean-copy check passes or with images or attachments, ending the turn before the draft check passes, editing `LEGAL.md` during a deal, and adding contract records to git. Details and a sample for your repository's settings: [docs/guardrails.md](docs/guardrails.md).

## Changes and releases
See [CHANGELOG.md](CHANGELOG.md), including the conditions for 1.0.0.

## License
MIT

---

## 日本語

相手から届いた契約書（まず NDA）を、Claude Code で「受け取り → 自社の直し → 相手との往復 → 署名」まで回すためのプラグインです。

### できること
- 相手の .docx に、自社の修正案を変更履歴（挿入・削除）として入れ、修正ごとの理由を Word のコメントとして付ける
- 送る前に、社内の検証役が直しを確かめる。見方は4つ（自社の弁護士・相手の法務・形式・生成 AI 条項）
- 相手へ送る清書と、返信メールの本文を道具で作る（手で書かない）
- 台帳（`register.csv`）に、契約ごとの状態・版・往復の回数を記録する

### 前提
- **Claude Code**（端末・デスクトップ・IDE）。claude.ai のチャットでは動かない（道具を手元で動かすため）。
- **Python 3.13**（標準ライブラリだけ。仮想環境もほかの部品も要らない）と **git**。
- Claude の **Google ドライブと Gmail のつながり**（原本・社内用の Google ドキュメント・返信の下書きのため）。
- **日本語の契約（.docx）と日本の実務向け**。一般の法務レビューのプラグインと違い、.docx そのものを直し、送る前の確認を Hook で止める。

### 入れ方
ターミナルで打ちます。`--scope user` にすると、この Mac の全部のプロジェクトで使えます。

```bash
claude plugin marketplace add AXSC-Studio/axla-inc-plugins
claude plugin install axla-legal@axla-inc-plugins --scope user
```

1つのリポジトリでチームと共有したいときは、そのリポジトリで2行目を `--scope project` にして打ちます（そのリポジトリの設定に書かれるので、コミットします）。

### 通信先
| 送り先 | 何を | なぜ |
|---|---|---|
| あなたが使う Claude のモデル | Claude が読む文（契約書・決まり・記録） | ほかの Claude Code のセッションと同じ |
| あなたの Google ドライブ（つながり） | 原本を読む。社内用の Google ドキュメントを作る | 代表や法務の担当が見るため |
| あなたの Gmail（つながり） | 返信の下書きを作って読む | 送信は必ず人が押す |
| Google ドライブの API（任意） | `resolve_comments.py`（あなた自身の `gcloud` のトークン） | 前からある Google ドキュメントを直すときだけ |
| あなたの Claude のルーティン（任意・試験中） | `notify_reply.gs` が Gmail のスレッド ID だけを送る | 返事が来たら、読むだけの見張りを起こすため（[routines/reply-watcher.md](routines/reply-watcher.md)）。beta の API を使うので、予告なく動かなくなることがある |

Hook は手元だけで動きます。Axla Inc. には何も送りません。くわしくは [PRIVACY.md](PRIVACY.md)。

### データの扱い
- 契約ごとの記録は、あなたのリポジトリの `loop/legal/contracts/<ID>/` に置き、git の除外に入れる（入っていなければ道具が止まる）。台帳には相手の名前を書かない。
- `view.py` などは契約の本文を画面に出すので、本文がセッションの記録に残る。セッションは自分だけのものにしておく。
- 往復ごとに作業フォルダを消す（`rm -rf "$W"`）。契約が要らなくなったら、記録フォルダも消す。

### 困ったとき
- **「loop/legal/contracts/ が git の除外に入っていない」**：`templates/gitignore.txt` の1行を `.gitignore` に足す。
- **「作成者名がない」**：`templates/config.json` を `loop/legal/config.json` に写して、自社の値を書く。
- **Hook に止められた**：理由を読む。足りない確認（清書・下書きの検査 …）の名前が出ているので、回り道をせず、その手順をやる。
- **シェルで `${CLAUDE_PLUGIN_ROOT}` が空**：スキルの中でしか置き換わらない。スキルに出ている絶対パスを使う。
- **下書きの検査が走らない**：`get_draft` を `messageFormat=RAW` で読む。Hook が検査する。

### 使い方
1. 入れる（上の「入れ方」）
2. 使う側のリポジトリに `loop/legal/` を作り、自社の決まり `LEGAL.md` と台帳 `register.csv` を置く（列は [docs/register.md](docs/register.md)）
3. そのリポジトリの `.gitignore` に `loop/legal/contracts/` の1行を足す（無いと道具が止まる）
4. `/axla-legal:loop` と打つ（または「この契約書を見て」と頼む）。入口が契約ごとにいまどこかを読み、次の1歩だけを進める：`intake` → `redline-contract` → `review` → `gdoc` → `send` → `learn`。人を待つ所（最終 OK・送信・署名）では止まって知らせる

契約書の本文と契約ごとの記録は、このプラグインにも git にも入れません。送信・署名・決まりの外の判断は、必ず人が行います。

### 5分で試す（Google のアカウントは要らない）
`examples/` に、架空の会社どうしのダミーの NDA、直しの見本（`Redline Data.json`）、検証役の出力の見本があります。端末で、`T` にこのプラグインの `scripts` フォルダ、`E` に `examples` フォルダを入れて：

```bash
W=$(mktemp -d)
python3 -I -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$E/example-nda.docx" "$W/work"
python3 -I "$T/redline.py" "$W/work" "$E/Redline Data.json"        # 変更履歴を入れる
python3 -I "$T/view.py" "$W/work" changed                           # 変わった所を見る
python3 -I "$T/check_refs.py" "$W/work" --out "$W/review-refs.md"   # 条・項の参照
cp "$E/review-sample.md" "$W/review-a.md"
python3 -I "$T/count_findings.py" "$W"/review-*.md                  # 合否を道具で数える
python3 -I "$T/make_clean.py" "$W/work" --out "$W/clean.docx"       # 相手に送る清書
python3 -I "$T/make_reply.py" "$E/Redline Data.json" --out-text "$W/reply.txt" --out-html "$W/reply.html"
```

自社のリポジトリに置くひな形は `templates/` にあります（`LEGAL.md`・`register.csv`・自社名と変更履歴の作成者名を書く `config.json`・`.gitignore` の1行）。プラグインの中に、特定の会社の決め打ちはありません。

### 例のプロンプト
- 「新しい取引先から NDA が届いた。`/axla-legal:loop`」：受け取りから始め、直しと検証へ進む。
- 「NDA の直しに相手から返事が来た。次は？ `/axla-legal:loop 261123_NDA_1`」：相手の版を読み、次の往復を回す。
- 「最終 OK を出した。返信の下書きを作って、送る前に確かめて」：清書と返信文を作り、送る前の検査を通す（送信はあなたが押す）。

### 柵（Hook）
頼むだけでなく、道具で止めます。契約の相手へのメールの送信、清書の検査が通る前や画像・添付のある返信の下書き、下書きの確認が通る前にターンを終えること、中間ループの間の `LEGAL.md` の書き換え、契約の記録の `git add` を止めます。くわしくと、利用側の設定の見本は [docs/guardrails.md](docs/guardrails.md)。

### 変更履歴とリリース
[CHANGELOG.md](CHANGELOG.md)（1.0.0 を出す条件も）。

### ライセンス
MIT
