# axla-inc-plugins

**English** | [日本語](#日本語)

Claude Code plugins that Axla Inc. builds and uses to run an AI-native company. Each plugin is one department; each skill inside it is one job.

| Plugin | Display name | Department | Skill | What it does |
|---|---|---|---|---|
| [axla-legal](plugins/axla-legal/) | Axla Legal | Back office | `/axla-legal:redline-contract` | Redlines a contract you received with tracked changes and comments, and runs the back-and-forth until signature |
| [axla-marketing](plugins/axla-marketing/) | Axla Marketing | Marketing | `/axla-marketing:meeting-to-article` | Turns the notes of a solo Google Meet into a draft article |

## Install

```
/plugin marketplace add AXSC-Studio/axla-inc-plugins
/plugin install axla-legal@axla-inc-plugins
```

## Naming rules
1. **One plugin = one department.** Names are `axla-` + department (`axla-legal`, `axla-marketing`). Plain words alone are held for review in the directory and clash easily with other companies' plugins. The display name goes in `displayName` (for example "Axla Legal").
2. **One skill = one job.** Names are verb-noun or input-to-output (`redline-contract`, `meeting-to-article`). No "loop" and no department name in skill names.
3. **Published names do not change.** Departments are expressed with `category` and `keywords` in `marketplace.json` and in the table above. Old names are mapped in `renames` (`legal-loop` → `axla-legal`).

## Where your data lives
Plugins contain tools only. Each company's own data (its rules `LEGAL.md`, its ledger `register.csv`, per-contract records) lives in the using repository under `loop/<name>/`. Contract text never goes into a plugin or into git.

## License
MIT

---

## 日本語

Axla Inc. が「AI ネイティブカンパニー」を回すために作って使っている、Claude Code のプラグイン集です。プラグインは1つで1部署、その中のスキルは1つで1つの仕事です。

| プラグイン | 表示名 | 部署 | スキル | 何をするか |
|---|---|---|---|---|
| [axla-legal](plugins/axla-legal/) | Axla Legal | Back office | `/axla-legal:redline-contract` | 相手から届いた契約書に、変更履歴とコメントで修正案を入れ、署名まで往復を回す |
| [axla-marketing](plugins/axla-marketing/) | Axla Marketing | Marketing | `/axla-marketing:meeting-to-article` | 一人で話した Google Meet のメモを、記事の下書きにする |

### 入れ方

```
/plugin marketplace add AXSC-Studio/axla-inc-plugins
/plugin install axla-legal@axla-inc-plugins
```

### 名前の決まり
1. **プラグイン＝部署。** 名前は `axla-` ＋部署名（`axla-legal`、`axla-marketing`）にする。ありふれた言葉だけの名前は、ディレクトリの審査に回り、ほかの会社の名前ともぶつかりやすいため。表示名は `displayName` で付ける（例「Axla Legal」）。
2. **スキル＝仕事1つ。** 名前は「動詞-名詞」か「入力-to-出力」（`redline-contract`、`meeting-to-article`）。`loop` という語や部署名は、スキル名に入れない。
3. **一度公開した名前は変えない。** 部署は、`marketplace.json` の `category`・`keywords` と上の表で表す。旧名からの移り先は `renames` に書く（`legal-loop` → `axla-legal`）。

### データの置き場所
プラグインには道具だけを入れます。会社ごとのデータ（決まりの `LEGAL.md`・台帳の `register.csv`・契約ごとの記録）は、使う側のリポジトリの `loop/<名前>/` に置きます。契約書の本文は、プラグインにも git にも入れません。

### ライセンス
MIT
