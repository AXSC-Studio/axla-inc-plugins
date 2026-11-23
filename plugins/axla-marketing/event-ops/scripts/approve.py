#!/usr/bin/env python3
"""まとめ承認（承認ゲート・送信）。spec 002。

人が自分の端末で動かす道具。AI が代わりに承認できないように、次の2つで守る。
- 確認は端末（/dev/tty）から直接読む。端末の無い場所（Claude Code の Bash・CI）では書かずに止まる（exit 2）
- 承認するには、表示された承認 ID を人が打ち込む。--yes のような省略はない
承認ファイルへの AI の直接の書き込みは、hooks/guard_send.py が止める。

使い方
  python3 approve.py new  --event <イベントのフォルダ> --kit <凍結した版の URL> --sha256 <その版のハッシュ>
                          --to PT-001,PT-002 --tools send_message[,create_blast] [--days 7]
  python3 approve.py show --event <イベントのフォルダ>
  python3 approve.py amend --event <イベントのフォルダ> --id A-001 --note "文面の小さな直し"
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def open_tty():
    if os.environ.get("EVENT_OPS_NO_TTY"):
        return None
    try:
        return open("/dev/tty", "r+", encoding="utf-8")
    except OSError:
        return None


def confirm(tty, summary, expected):
    tty.write(summary + "\n")
    tty.write(f"承認するなら {expected} と打ってください（それ以外で取りやめ）： ")
    tty.flush()
    return tty.readline().strip() == expected


def next_id(folder):
    nums = [int(m.group(1)) for f in folder.glob("A-*.json") if (m := re.match(r"A-(\d+)\.json$", f.name))]
    return f"A-{(max(nums) + 1) if nums else 1:03d}"


def cmd_new(a):
    event = Path(a.event)
    if not event.is_dir():
        sys.stderr.write(f"イベントのフォルダがありません：{event}\n")
        return 2
    if not re.fullmatch(r"[0-9a-f]{64}", a.sha256):
        sys.stderr.write("--sha256 は 64 桁の16進数にしてください\n")
        return 2
    to = [x.strip() for x in a.to.split(",") if x.strip()]
    if not to or not all(re.fullmatch(r"PT-\d{3,}", x) for x in to):
        sys.stderr.write("--to は相手の番号（PT-001 の形）をカンマで並べてください。名前やメールは書きません\n")
        return 2
    tools = [x.strip() for x in a.tools.split(",") if x.strip()]
    tty = open_tty()
    if tty is None:
        sys.stderr.write("承認は、人が自分の端末で動かしたときだけ書けます（端末が見つかりません）。何も書いていません\n")
        return 2
    folder = event / "approvals"
    folder.mkdir(exist_ok=True)
    aid = next_id(folder)
    now = datetime.now(timezone.utc)
    data = {
        "id": aid,
        "kit": {"url": a.kit, "sha256": a.sha256},
        "to": to,
        "tools": tools,
        "approved_by": os.environ.get("USER", "human"),
        "approved_at": now.isoformat(timespec="seconds"),
        "expires_at": (now + timedelta(days=a.days)).isoformat(timespec="seconds"),
        "amendments": [],
    }
    summary = (
        f"\n— まとめ承認 {aid} —\n"
        f"  版   : {a.kit}\n  ハッシュ: {a.sha256[:12]}…\n"
        f"  宛先 : {', '.join(to)}\n  道具 : {', '.join(tools)}\n  期限 : {a.days} 日"
    )
    if not confirm(tty, summary, aid):
        sys.stderr.write("取りやめました。何も書いていません\n")
        return 1
    (folder / f"{aid}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{aid} を書きました：{folder / (aid + '.json')}")
    return 0


def cmd_show(a):
    folder = Path(a.event) / "approvals"
    now = datetime.now(timezone.utc)
    files = sorted(folder.glob("A-*.json")) if folder.is_dir() else []
    if not files:
        print("承認はまだありません")
        return 0
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        try:
            live = datetime.fromisoformat(d.get("expires_at", "")) > now
        except ValueError:
            live = False
        state = "有効" if live else "期限切れ"
        print(f"{d.get('id')}  {state}  宛先 {', '.join(d.get('to', []))}  道具 {', '.join(d.get('tools', []))}  直し {len(d.get('amendments', []))} 件")
    return 0


def cmd_amend(a):
    f = Path(a.event) / "approvals" / f"{a.id}.json"
    if not f.exists():
        sys.stderr.write(f"{a.id} がありません\n")
        return 2
    tty = open_tty()
    if tty is None:
        sys.stderr.write("直しの追記も、人が自分の端末で動かしたときだけ書けます。何も書いていません\n")
        return 2
    d = json.loads(f.read_text(encoding="utf-8"))
    if not confirm(tty, f"\n— {a.id} に直しを追記 —\n  {a.note}", a.id):
        sys.stderr.write("取りやめました\n")
        return 1
    d.setdefault("amendments", []).append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": a.note})
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{a.id} に直しを追記しました（朝の知らせに出ます）")
    return 0


def main():
    p = argparse.ArgumentParser(description="まとめ承認（人が自分の端末で動かす）")
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--event", required=True)
    n.add_argument("--kit", required=True)
    n.add_argument("--sha256", required=True)
    n.add_argument("--to", required=True)
    n.add_argument("--tools", required=True)
    n.add_argument("--days", type=int, default=7)
    s = sub.add_parser("show")
    s.add_argument("--event", required=True)
    m = sub.add_parser("amend")
    m.add_argument("--event", required=True)
    m.add_argument("--id", required=True)
    m.add_argument("--note", required=True)
    a = p.parse_args()
    return {"new": cmd_new, "show": cmd_show, "amend": cmd_amend}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
