# Privacy policy (Axla Legal)

**English** | [日本語](#日本語)

Last updated: 2026-11-23

Axla Legal is a Claude Code plugin made of skills, local scripts and hooks. **The plugin itself does not collect, send or store any data on servers run by Axla Inc. or anyone else.** Axla Inc. never receives your contracts, emails or records.

## What the plugin handles, and where it stays
| Data | Where it is | Who can see it |
|---|---|---|
| The contract (.docx), the internal Google Doc, the clean copy | Your Google Drive, and a temporary work folder on your computer | You, and the people you share your Drive folder with |
| Per-contract records (`Redline Data.json`, `loop-log.md`, `gate.json` with the counterparty's email address, `reply.txt`) | `loop/legal/contracts/<id>/` in your own repository, which must be git-ignored (the tools stop if it is not) | You |
| Your rules (`LEGAL.md`), the ledger (`register.csv`, no counterparty names) | `loop/legal/` in your own repository | Whoever can read that repository |
| Reply drafts | Your Gmail drafts (sending is always done by you) | You |

## What goes to outside services
The plugin only uses services **you** connect and sign in to:
- **Claude (Anthropic)**: like any Claude Code session, the text Claude reads (the contract, your rules, the records) is sent to the model you use, under your agreement with Anthropic.
- **Google Drive and Gmail connectors**: to read the original, create the internal Google Doc, and create and read reply drafts in your account.
- **Optional**: `resolve_comments.py` calls the Google Drive API with your own `gcloud` token; the optional Apps Script (`notify_reply.gs`) sends only a Gmail thread ID to your own Claude routine.

The hooks run only on your computer. Nothing is sent to Axla Inc.

## Deleting data
Delete the work folder after each round, the record folder `loop/legal/contracts/<id>/` when you no longer need it, and drafts or Google Docs in your own accounts. The plugin keeps no copy anywhere else.

## Contact
Questions: open an issue at https://github.com/AXSC-Studio/axla-inc-plugins/issues (do not include contract text or names).

---

## 日本語

# プライバシーポリシー（Axla Legal）

最終更新：2026-11-23

Axla Legal は、スキル・手元で動くスクリプト・Hook でできた Claude Code のプラグインです。**プラグインそのものは、Axla Inc. やほかの誰かのサーバーに、データを集めたり、送ったり、保存したりしません。** Axla Inc. が、あなたの契約書・メール・記録を受け取ることはありません。

## プラグインが扱うものと、その置き場所
| データ | 置き場所 | 見られる人 |
|---|---|---|
| 契約書（.docx）・社内用の Google ドキュメント・清書 | あなたの Google ドライブと、あなたのパソコンの一時的な作業フォルダ | あなたと、ドライブのフォルダを共有した人 |
| 契約ごとの記録（`Redline Data.json`・`loop-log.md`・相手のメールアドレスが入る `gate.json`・`reply.txt`） | あなたのリポジトリの `loop/legal/contracts/<ID>/`。git の除外に入れる（入っていなければ道具が止まる） | あなた |
| 自社の決まり（`LEGAL.md`）・台帳（`register.csv`。相手の名前は書かない） | あなたのリポジトリの `loop/legal/` | そのリポジトリを読める人 |
| 返信の下書き | あなたの Gmail の下書き（送信は必ずあなたが押す） | あなた |

## 外のサービスに送るもの
プラグインが使うのは、**あなたが**つないでログインしたサービスだけです。
- **Claude（Anthropic）**：ほかの Claude Code のセッションと同じく、Claude が読む文（契約書・決まり・記録）は、あなたが使うモデルに、あなたと Anthropic の契約のもとで送られます。
- **Google ドライブと Gmail のつながり**：原本を読む、社内用の Google ドキュメントを作る、返信の下書きを作って読むため。あなたのアカウントの中だけです。
- **任意**：`resolve_comments.py` は、あなた自身の `gcloud` のトークンで Google ドライブの API を呼びます。任意の Apps Script（`notify_reply.gs`）は、Gmail のスレッド ID だけを、あなた自身の Claude のルーティンに送ります。

Hook は、あなたのパソコンの中だけで動きます。Axla Inc. には何も送りません。

## 消し方
往復ごとに作業フォルダを消し、要らなくなったら記録フォルダ `loop/legal/contracts/<ID>/` を消し、下書きや Google ドキュメントはあなたのアカウントで消してください。プラグインは、ほかのどこにも写しを持ちません。

## 問い合わせ
https://github.com/AXSC-Studio/axla-inc-plugins/issues に Issue を立ててください（契約の本文や名前は書かないでください）。
