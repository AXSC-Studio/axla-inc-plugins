# axla-inc-plugins

Axla Inc. が「AI ネイティブカンパニー」を作るために使っている Claude Code のプラグイン集です。

| プラグイン | 表示名 | 部署（サイドバー） | スキル | 何をするか |
|---|---|---|---|---|
| [axla-legal](plugins/axla-legal/) | Axla Legal | Back office | `/axla-legal:redline-contract` | 相手から届いた契約書に、変更履歴とコメントで修正案を入れ、署名まで往復を回す |
| [axla-marketing](plugins/axla-marketing/) | Axla Marketing | Marketing | `/axla-marketing:meeting-to-article` | 一人で話した Google Meet のメモを、記事の下書きにする |

## 名前の決まり（3行ルール）
1. **プラグイン＝部署。** 名前は `axla-` ＋部署名（`axla-legal`、`axla-marketing`）。ありふれた言葉だけの名前はディレクトリの審査に回り、ほかの会社の名前ともぶつかりやすいため。表示名は `displayName` で付ける（例「Axla Legal」）。
2. **スキル＝仕事1つ。** 名前は「動詞-名詞」か「入力-to-出力」（`redline-contract`）。`loop` という語や部署名はスキル名に入れない。
3. **一度公開した名前は変えない。** 部署とサイドバーの対応は、`marketplace.json` の `category`・`keywords` と、上の表で表す。

旧名からの移り先は `marketplace.json` の `renames` に書く（`legal-loop` → `axla-legal`）。

## 入れ方

```
/plugin marketplace add AXSC-Studio/axla-inc-plugins
/plugin install axla-legal@axla-inc-plugins
```

## データの置き場所
プラグインは道具だけです。会社ごとのデータ（決まりの LEGAL.md・台帳 register.csv・契約ごとの記録）は、使う側のリポジトリの `loop/legal/` に置きます。契約書の本文はプラグインにも git にも入れません。

## ライセンス
MIT
