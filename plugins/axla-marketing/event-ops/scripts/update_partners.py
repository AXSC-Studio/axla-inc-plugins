#!/usr/bin/env python3
"""相手の台帳を進める（中間ループの検証器と状態ストア）。spec 005。

台帳 loop/marketing/event-ops/partners.csv（git に入れる。番号だけ・実名なし）を、この道具だけが書く。
状態：contacted（連絡した）→ sent（送った）→ replied（返事が来た）→ confirmed（確定）／ declined（断り）

使い方（どれも --event <イベントのフォルダ> を付ける）
  add       --partner PT-001 --kind venue|speaker|sponsor|catering|sound|other
  sent      --partner PT-001          # 送った（見張りが送信済みを拾ったとき、または manual の人が入れる）
  replied   --partner PT-001
  offline   --partner PT-001 --note "電話で決まったこと"   # 電話・対面・チャットで決まったこと
  confirmed --partner PT-001          # 確定（会場なら G2 の記録。state.json の g2_confirmed を true に）
  declined  --partner PT-001
  overdue   --days 3                  # 送ってから返事の無い相手。いれば exit 1（朝の知らせ）
  draft     --partner PT-001 --file <返事の下書き>   # 下書きを、いまの計画のハッシュと一緒に登録
  stale                               # 計画（plan.md・budget.json・event.json）が変わった下書きに【古い】を付けて exit 1
"""
import argparse
import csv
import hashlib
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402

FIELDS = ["id", "kind", "event", "status", "last_contact", "next_time"]
KINDS = {"venue", "speaker", "sponsor", "catering", "sound", "other"}
PLAN_FILES = ["plan.md", "budget.json", "event.json"]
STALE = "【古い】"


def ledger(event):
    return lib.base_of_event(event) / "partners.csv"


def read_rows(event):
    f = ledger(event)
    if not f.exists():
        return []
    with open(f, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_rows(event, rows):
    with open(ledger(event), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def plan_hash(event):
    h = hashlib.sha256()
    for name in PLAN_FILES:
        p = Path(event) / name
        h.update(name.encode())
        h.update(p.read_bytes() if p.exists() else b"")
    return h.hexdigest()


def set_status(event, pid, status, note=None):
    rows = read_rows(event)
    row = next((r for r in rows if r["id"] == pid and r.get("event") == Path(event).name), None)
    if row is None:
        row = {"id": pid, "kind": "other", "event": Path(event).name}
        rows.append(row)
    row["status"] = status
    row["last_contact"] = date.today().isoformat()
    write_rows(event, rows)
    line = f"- {date.today().isoformat()} {pid}（{row.get('kind', 'other')}）：{status}" + (f"。{note}" if note else "")
    lib.append_to_section(Path(event) / "event-log.md", "相手ごとの状態", line)
    lib.record_run(lib.base_of_event(event), "middle", "state_store", status, None, partner=pid)
    return row


def main():
    p = argparse.ArgumentParser(description="相手の台帳を進める")
    p.add_argument("cmd", choices=["add", "sent", "replied", "offline", "confirmed", "declined", "overdue", "draft", "stale"])
    p.add_argument("--event", required=True)
    p.add_argument("--partner")
    p.add_argument("--kind", default="other")
    p.add_argument("--note")
    p.add_argument("--days", type=int, default=3)
    p.add_argument("--file")
    a = p.parse_args()
    event = Path(a.event)

    if a.cmd in ("add", "sent", "replied", "offline", "confirmed", "declined", "draft"):
        if not a.partner or not re.fullmatch(r"PT-\d{3,}", a.partner):
            sys.stderr.write("相手は番号（PT-001 の形）で書いてください。名前は names.local にだけ置きます\n")
            return 2

    if a.cmd == "add":
        if a.kind not in KINDS:
            sys.stderr.write(f"--kind は {', '.join(sorted(KINDS))} のどれか\n")
            return 2
        rows = read_rows(event)
        if not any(r["id"] == a.partner and r.get("event") == event.name for r in rows):
            rows.append({"id": a.partner, "kind": a.kind, "event": event.name, "status": "contacted", "last_contact": date.today().isoformat()})
            write_rows(event, rows)
        print(f"{a.partner}（{a.kind}）を台帳に足しました")
        return 0

    if a.cmd in ("sent", "replied", "declined"):
        set_status(event, a.partner, a.cmd)
        print(f"{a.partner}：{a.cmd}")
        return 0

    if a.cmd == "offline":
        set_status(event, a.partner, "replied", note=f"（電話・対面など）{a.note or ''}")
        print(f"{a.partner}：電話・対面などで決まったことを記録しました")
        return 0

    if a.cmd == "confirmed":
        row = set_status(event, a.partner, "confirmed")
        if row.get("kind") == "venue":
            st = lib.load_json(event / "state.json", {})
            st["g2_confirmed"] = True
            lib.save_json(event / "state.json", st)
            print("会場が確定しました（G2 の記録）。【仮】が残っていれば check_kit.py が開催へ進むのを止めます")
        else:
            print(f"{a.partner}：confirmed")
        return 0

    if a.cmd == "overdue":
        today = date.today()
        late = []
        for r in read_rows(event):
            if r.get("event") != event.name or r.get("status") != "sent":
                continue
            try:
                days = (today - date.fromisoformat(r.get("last_contact", ""))).days
            except ValueError:
                continue
            if days > a.days:
                late.append((r["id"], days))
        if late:
            print(f"返事待ちが {a.days} 日を超えた相手：" + "、".join(f"{pid}（{d} 日）" for pid, d in late))
            lib.record_run(lib.base_of_event(event), "middle", "trigger", "overdue", "reply_wait", count=len(late))
            return 1
        print("返事待ちの超過はありません")
        return 0

    if a.cmd == "draft":
        f = Path(a.file or "")
        if not f.exists():
            sys.stderr.write("--file の下書きがありません\n")
            return 2
        drafts = lib.load_json(event / "drafts.json", {})
        drafts[str(f.resolve().relative_to(event.resolve()))] = {"partner": a.partner, "plan_hash": plan_hash(event), "at": lib.now_iso()}
        lib.save_json(event / "drafts.json", drafts)
        print(f"下書きを登録しました（{a.partner}）")
        return 0

    if a.cmd == "stale":
        drafts = lib.load_json(event / "drafts.json", {})
        now_hash = plan_hash(event)
        stale = []
        for rel, d in drafts.items():
            if d.get("plan_hash") != now_hash and not d.get("stale"):
                path = event / rel
                if path.exists():
                    text = path.read_text(encoding="utf-8")
                    if not text.startswith(STALE):
                        path.write_text(f"{STALE} 計画が変わったので、このまま送らない。plan-event で計算し直してから作り直す\n\n" + text, encoding="utf-8")
                d["stale"] = True
                stale.append(rel)
        lib.save_json(event / "drafts.json", drafts)
        if stale:
            print("計画が変わったので【古い】にした下書き：" + "、".join(stale))
            lib.record_run(lib.base_of_event(event), "middle", "verifier", "stale", "plan_changed", count=len(stale))
            return 1
        print("古い下書きはありません")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
