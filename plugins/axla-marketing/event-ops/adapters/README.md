# 差し込み口（adapters）

スキルは道具の種類名（`~~events`・`~~docs`・`~~email`）で書き、どの道具を使うかは使う側の `config.json` の `adapters` で選ぶ。既定はどれも `manual`（何もつながなくても1周目が回る）。

| 種類 | 既定 | 用意しているもの |
|---|---|---|
| `~~events`（告知） | [manual](events/manual.md) | [luma](events/luma.md)（公式 MCP） |
| `~~docs`（資料） | [manual](docs/manual.md) | [artifact](docs/artifact.md) |
| `~~email` | manual | gmail（spec 006） |

どの差し込み口でも、送信・公開・共有は spec 002 の hook が止める（人のまとめ承認が要る）。
