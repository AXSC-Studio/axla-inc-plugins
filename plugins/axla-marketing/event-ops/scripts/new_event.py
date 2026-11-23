#!/usr/bin/env python3
"""イベントのフォルダを作る（内側の起動トリガー）。spec 003。

- events/<yymmdd_英語の名前>/ を作り、ひな形を写す。使う側の templates/ があればそちらを優先する（外側の学びがここに戻る）
- 初めて使うリポなら、EVENTS.md・config.json・台帳の見出しも置く
- checklist.json は全項目「未達」から始まる
- adopt：すでに送った版がある途中のイベントを取り込む（v1.0 として sent/ と partners.csv に書く）

使い方
  python3 new_event.py init  --id 261211_startup-night
  python3 new_event.py adopt --id 261211_startup-night --partner PT-001:venue --sent PT-001:<URL>:<sha256>
  （どちらも、使う側のリポのいちばん上で動かす）
"""
import argparse
import csv
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402

PLUGIN_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
PER_EVENT = ["plan.md", "event-log.md", "checklist.json", "budget.json", "state.json", "event.json", "run-sheet.md"]
BOOTSTRAP = ["EVENTS.md", "config.json", "register.csv", "partners.csv", "names.local.example"]


def template(base, name):
    user = base / "templates" / name
    return user if user.exists() else PLUGIN_TEMPLATES / name


def bootstrap(base):
    base.mkdir(parents=True, exist_ok=True)
    for name in BOOTSTRAP:
        if not (base / name).exists():
            shutil.copyfile(PLUGIN_TEMPLATES / name, base / name)


def cmd_init(a, quiet=False):
    if not lib.EVENT_ID.match(a.id):
        sys.stderr.write("イベント ID は yymmdd_英語の名前（小文字・数字・ハイフン）にしてください\n")
        return 2
    base = Path.cwd() / lib.DATA_DIR
    bootstrap(base)
    event = base / "events" / a.id
    if event.exists():
        sys.stderr.write(f"{a.id} はもうあります。呼び直しは plan-event の手順で\n")
        return 1
    event.mkdir(parents=True)
    for d in ("kit", "reviews", "evidence", "approvals", "sent"):
        (event / d).mkdir()
    for name in PER_EVENT:
        text = template(base, name).read_text(encoding="utf-8").replace("{{EVENT_ID}}", a.id)
        (event / name).write_text(text, encoding="utf-8")
    config = lib.load_json(base / "config.json", {})
    st = lib.load_json(event / "state.json", {})
    st["max_rounds"] = int(config.get("max_rounds", st.get("max_rounds", 3)))
    lib.save_json(event / "state.json", st)
    data = lib.load_checklist(event)
    for i in data.get("items", []):
        i["passes"], i["evidence"] = False, None  # どのひな形から来ても、未達から始める
    lib.save_json(lib.checklist_path(event), data)
    with open(base / "register.csv", "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([a.id, "planning", lib.now_iso()[:10], "", "", "", "", ""])
    lib.record_run(base, "inner", "trigger", "event_created", None, event=a.id)
    if not quiet:
        print(f"{a.id} を作りました：{event}")
        print("次：plan.md を埋め、budget.json を直して recalc_budget.py --event で収支を出す")
    return 0


def cmd_adopt(a):
    base = Path.cwd() / lib.DATA_DIR
    event = base / "events" / a.id
    if not event.exists():
        code = cmd_init(a, quiet=True)
        if code:
            return code
    kinds = {}
    for spec in a.partner or []:
        pid, _, kind = spec.partition(":")
        if not re.fullmatch(r"PT-\d{3,}", pid):
            sys.stderr.write(f"相手は番号で書いてください：{pid}\n")
            return 2
        kinds[pid] = kind or "other"
    rows = []
    for spec in a.sent or []:
        m = re.fullmatch(r"(PT-\d{3,}):(https?://\S+):([0-9a-f]{64})", spec)
        if not m:
            sys.stderr.write("--sent は PT-001:<URL>:<sha256> の形で\n")
            return 2
        pid, url, sha = m.groups()
        lib.save_json(event / "sent" / f"{pid}_v1.0.json", {"url": url, "sha256": sha, "partner": pid, "adopted": True})
        rows.append(pid)
    with open(base / "partners.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for pid in sorted(set(kinds) | set(rows)):
            w.writerow([pid, kinds.get(pid, "other"), a.id, "sent" if pid in rows else "contacted", lib.now_iso()[:10], ""])
    lib.append_to_section(event / "event-log.md", "既定値で決めたこと", f"- {lib.now_iso()[:10]} 途中から取り込んだ（送った版 {len(rows)} 件を v1.0 とした）")
    lib.record_run(base, "inner", "trigger", "event_adopted", None, event=a.id, sent=len(rows))
    print(f"{a.id} に取り込みました（送った版 {len(rows)} 件・相手 {len(set(kinds) | set(rows))} 者）")
    return 0


def main():
    p = argparse.ArgumentParser(description="イベントのフォルダを作る")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--id", required=True)
    d = sub.add_parser("adopt")
    d.add_argument("--id", required=True)
    d.add_argument("--partner", action="append")
    d.add_argument("--sent", action="append")
    a = p.parse_args()
    return {"init": cmd_init, "adopt": cmd_adopt}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
