# axla-inc-plugins

**English** | [日本語](#日本語)

Claude Code plugins that Axla Inc. builds and uses to run an AI-native company. Each plugin is one department; each skill inside it is one job.

| Plugin | Display name | Department | Skill | What it does |
|---|---|---|---|---|
| [axla-legal](plugins/axla-legal/) | Axla Legal | Back office | `/axla-legal:loop` | Redlines a contract you received with tracked changes and comments, and runs the back-and-forth until signature |
| [axla-marketing](plugins/axla-marketing/) | Axla Marketing | Marketing | `/axla-marketing:meeting-to-article`<br>`/axla-marketing:plan-event` (specs only) | Turns the notes of a solo Google Meet into a draft article. Runs an in-person event you host (event-ops, specs only) |

## Install

Run in your terminal. `--scope user` makes it available in every project on this Mac.

```bash
claude plugin marketplace add AXSC-Studio/axla-inc-plugins
claude plugin install axla-legal@axla-inc-plugins --scope user
```

To share it with your team through one repository instead, run the install line there with `--scope project` (it is written to that repository's settings, which you commit).

## Naming rules
1. **One plugin = one department.** Names are `axla-` + department (`axla-legal`, `axla-marketing`). Plain words alone are held for review in the directory and clash easily with other companies' plugins. The display name goes in `displayName` (for example "Axla Legal").
- **Inside a plugin, one folder per feature.** A feature folder holds its own `skills/`, `specs/`, `scripts/` and `prompts/` (for example `plugins/axla-marketing/event-ops/`). The plugin's `plugin.json` lists each feature's `skills/` folder.
2. **One skill = one job.** Names are verb-noun or input-to-output (`redline-contract`, `meeting-to-article`). No "loop" and no department name in skill names.
3. **Published names do not change.** `category` in `marketplace.json` is the department name in lowercase (`legal`, `marketing`). The sidebar section (for example Legal → Back office) is shown by `keywords` and the Department column in the table above. Old names are mapped in `renames` (`legal-loop` → `axla-legal`).

## Where your data lives
Plugins contain tools only. Each company's own data (its rules `LEGAL.md`, its ledger `register.csv`, per-contract records) lives in the using repository under `loop/<name>/`. Contract text never goes into a plugin or into git.

## Versioning
Each plugin follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) and is versioned on its own.

| Bump | When | Example |
|---|---|---|
| PATCH (`0.2.0` → `0.2.1`) | Wording, README or description only. Behavior does not change | Translating descriptions to English |
| MINOR (`0.2.1` → `0.3.0`) | A new skill, a change in behavior, or a rename | Renaming `legal-loop` to `axla-legal` |
| MAJOR (`0.x` → `1.0.0`) | We promise outside users that we will not break them without notice | Not yet |

- While the version is `0.x`, anything may still change.
- Any change inside a plugin folder must bump that plugin's version. Without a bump, installed users do not receive the change.
- The version lives in one place only: the plugin's `.claude-plugin/plugin.json`.

## License
MIT

---

## 日本語

Axla Inc. が「AI ネイティブカンパニー」を回すために作って使っている、Claude Code のプラグイン集です。プラグインは1つで1部署、その中のスキルは1つで1つの仕事です。

| プラグイン | 表示名 | 部署 | スキル | 何をするか |
|---|---|---|---|---|
| [axla-legal](plugins/axla-legal/) | Axla Legal | Back office | `/axla-legal:loop` | 相手から届いた契約書に、変更履歴とコメントで修正案を入れ、署名まで往復を回す |
| [axla-marketing](plugins/axla-marketing/) | Axla Marketing | Marketing | `/axla-marketing:meeting-to-article`<br>`/axla-marketing:plan-event`（spec のみ） | 一人で話した Google Meet のメモを、記事の下書きにする。自分で開くイベントを回す（event-ops、spec のみ） |

### 入れ方

ターミナルで打ちます。`--scope user` にすると、この Mac の全部のプロジェクトで使えます。

```bash
claude plugin marketplace add AXSC-Studio/axla-inc-plugins
claude plugin install axla-legal@axla-inc-plugins --scope user
```

1つのリポジトリでチームと共有したいときは、そのリポジトリで2行目を `--scope project` にして打ちます（そのリポジトリの設定に書かれるので、コミットします）。

### 名前の決まり
1. **プラグイン＝部署。** 名前は `axla-` ＋部署名（`axla-legal`、`axla-marketing`）にする。ありふれた言葉だけの名前は、ディレクトリの審査に回り、ほかの会社の名前ともぶつかりやすいため。表示名は `displayName` で付ける（例「Axla Legal」）。
- **プラグインの中は、機能ごとに1フォルダ。** 機能のフォルダは、自分の `skills/`・`specs/`・`scripts/`・`prompts/` を持つ（例：`plugins/axla-marketing/event-ops/`）。プラグインの `plugin.json` に、各機能の `skills/` を並べる。
2. **スキル＝仕事1つ。** 名前は「動詞-名詞」か「入力-to-出力」（`redline-contract`、`meeting-to-article`）。`loop` という語や部署名は、スキル名に入れない。
3. **一度公開した名前は変えない。** `marketplace.json` の `category` は、部署名の小文字（`legal`・`marketing`）にそろえる。サイドバーの区分（例：Legal → Back office）は、`keywords` と上の表の「部署」の列で表す。旧名からの移り先は `renames` に書く（`legal-loop` → `axla-legal`）。

### データの置き場所
プラグインには道具だけを入れます。会社ごとのデータ（決まりの `LEGAL.md`・台帳の `register.csv`・契約ごとの記録）は、使う側のリポジトリの `loop/<名前>/` に置きます。契約書の本文は、プラグインにも git にも入れません。

### 版の付け方
プラグインごとに、世界標準の [Semantic Versioning](https://semver.org/lang/ja/)（`MAJOR.MINOR.PATCH`）で、別々に版を付けます。

| 上げる位置 | 上げるとき | 例 |
|---|---|---|
| PATCH（`0.2.0` → `0.2.1`） | 言葉・README・説明文の直しだけ。動きは変わらない | 説明文の英語化 |
| MINOR（`0.2.1` → `0.3.0`） | スキルを足す、動きを変える、名前を変える | `legal-loop` を `axla-legal` に改名 |
| MAJOR（`0.x` → `1.0.0`） | 外の利用者に「予告なしに壊さない」と約束するとき | まだ先 |

- 版が `0.x` のあいだは、まだ何でも変わりうる。
- プラグインのフォルダの中を1文字でも変えたら、そのプラグインの版を必ず上げる。上げないと、入れている人に届かない。
- 版は、そのプラグインの `.claude-plugin/plugin.json` の1か所にだけ書く。

### ライセンス
MIT
