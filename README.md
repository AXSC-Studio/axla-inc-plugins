# axla-inc-plugins

Axla Inc. が「AI ネイティブカンパニー」を作るために使っている Claude Code のプラグイン集です。

| プラグイン | 何をするか |
|---|---|
| [legal-loop](plugins/legal-loop/) | 相手から届いた契約書に、変更履歴とコメントで修正案を入れ、署名まで往復を回す |

## 入れ方

```
/plugin marketplace add AXSC-Studio/axla-inc-plugins
/plugin install legal-loop@axla-inc-plugins
```

## データの置き場所
プラグインは道具だけです。会社ごとのデータ（決まりの LEGAL.md・台帳 register.csv・契約ごとの記録）は、使う側のリポジトリの `loop/legal/` に置きます。契約書の本文はプラグインにも git にも入れません。

## ライセンス
MIT
