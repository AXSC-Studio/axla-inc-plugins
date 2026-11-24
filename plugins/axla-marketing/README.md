# Axla Marketing (`axla-marketing`)

**English** | [日本語](#日本語)

Axla's marketing desk as a Claude Code plugin. Install it once and you get every marketing feature below. Each feature lives in its own folder with its skills, rules (specs), tools and prompts.

| Feature | Skills | What it does | Status |
|---|---|---|---|
| [meeting-to-article](meeting-to-article/) | `/axla-marketing:meeting-to-article` | Turns the notes of a solo Google Meet into a draft article and an eye-catch image | Working |
| [event-ops](event-ops/) | `/axla-marketing:plan-event` and three more | Runs an in-person event you host: launch, back-and-forth with venue and sponsors, the day, follow-up, and learning for the next one | plan-event + coordinate-partners (specs 002–005) |

```
axla-marketing/
├── .claude-plugin/plugin.json   ← one manifest for the department
├── meeting-to-article/          ← feature: skills/ specs/ scripts/ prompts/
└── event-ops/                   ← feature: skills/ specs/ scripts/ prompts/ hooks/
```

## Install
Run in your terminal. `--scope user` makes it available in every project on this Mac.

```bash
claude plugin marketplace add AXSC-Studio/axla-inc-plugins
claude plugin install axla-marketing@axla-inc-plugins --scope user
```

To share it with your team through one repository instead, run the install line there with `--scope project` (it is written to that repository's settings, which you commit).

## Where your data lives
Plugins contain tools only. Your data lives in the using repository under `loop/marketing/` (event-ops uses `loop/marketing/event-ops/`).

## License
MIT

---

## 日本語

Axla のマーケティング部署を、Claude Code のプラグインにしたものです。1回入れると、下のマーケの機能がすべて使えます。機能は1つずつ自分のフォルダを持ち、その中にスキル・決まり（specs）・道具・指示文を置きます。

| 機能 | スキル | 何をするか | 状態 |
|---|---|---|---|
| [meeting-to-article](meeting-to-article/) | `/axla-marketing:meeting-to-article` | 一人で話した Google Meet のメモを、記事の下書きとアイキャッチにする | 使える |
| [event-ops](event-ops/) | `/axla-marketing:plan-event` ほか3つ | 自分で会場を借りて開くイベントを、立ち上げ・会場やスポンサーとのやりとり・当日・お礼・次回への学びまで回す | plan-event と coordinate-partners（spec 002〜005） |

### 入れ方
ターミナルで打ちます。`--scope user` にすると、この Mac の全部のプロジェクトで使えます。

```bash
claude plugin marketplace add AXSC-Studio/axla-inc-plugins
claude plugin install axla-marketing@axla-inc-plugins --scope user
```

1つのリポジトリでチームと共有したいときは、そのリポジトリで2行目を `--scope project` にして打ちます（そのリポジトリの設定に書かれるので、コミットします）。

### データの置き場所
プラグインは道具だけです。データは、使う側のリポジトリの `loop/marketing/` に置きます（event-ops は `loop/marketing/event-ops/`）。

### ライセンス
MIT
