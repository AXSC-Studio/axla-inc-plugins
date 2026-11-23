# redline-contract

**English** | [日本語](#日本語)

A feature of [Axla Legal](../README.md): runs a contract you received (starting with NDAs) from intake to signature. Install, requirements, data and network: see the [plugin README](../README.md).

| Folder | What is in it |
|---|---|
| [skills/](skills/) | The entry `loop` (`/axla-legal:loop`) and the parts `intake`, `redline-contract`, `review`, `gdoc`, `send`, `learn` |
| [specs/](specs/) | The rules of the contract loop (`legal-001`) |
| [scripts/](scripts/) | The tools, with a step-by-step [README](scripts/README.md) and tests |
| [hooks/](hooks/) | Guardrails ([docs/guardrails.md](docs/guardrails.md)) |
| [prompts/](prompts/) | Instructions for the reviewers |
| [docs/](docs/) | The ledger columns, the guardrails, the budget sample |
| [templates/](templates/) | Files to put in your own repository (`LEGAL.md`, `register.csv`, `config.json`, the `.gitignore` line) |
| [examples/](examples/) | A fictional NDA and samples for the 5-minute trial |
| [routines/](routines/) | The optional reply watcher |

---

## 日本語

[Axla Legal](../README.md) の機能の1つです。届いた契約書（まず NDA）を、受け取りから署名まで回します。入れ方・前提・通信先は、[プラグインの README](../README.md) を見てください。

| フォルダ | 中身 |
|---|---|
| [skills/](skills/) | 入口の `loop`（`/axla-legal:loop`）と、部品の `intake`・`redline-contract`・`review`・`gdoc`・`send`・`learn` |
| [specs/](specs/) | 契約のループの決まり（`legal-001`） |
| [scripts/](scripts/) | 道具。手順は [README](scripts/README.md)。テストもここ |
| [hooks/](hooks/) | 柵（[docs/guardrails.md](docs/guardrails.md)） |
| [prompts/](prompts/) | 検証役への指示文 |
| [docs/](docs/) | 台帳の列・柵・予算の見本 |
| [templates/](templates/) | 使う側のリポジトリに置くひな形（`LEGAL.md`・`register.csv`・`config.json`・`.gitignore` の1行） |
| [examples/](examples/) | 5分で試すための、作り話の NDA と見本 |
| [routines/](routines/) | 任意の、返事の見張り |
