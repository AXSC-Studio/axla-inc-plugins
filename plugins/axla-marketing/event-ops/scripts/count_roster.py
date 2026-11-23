#!/usr/bin/env python3
"""名簿から件数だけを数えて台帳に入れる（当日の計測）。spec 007。

名簿（告知サービスから書き出した CSV など）は名前と連絡先を含むので、数えたら捨てる（--delete）。
台帳 register.csv と記録には、件数だけを書く。

数えるもの
  applied   … 申し込みが通った人（approval_status が approved。列が無ければ全行）
  attended  … 来場した人（checked_in_at が入っている）
  consented … 後日の連絡などに同意した人（consent が yes / true / 1 / はい）
列の名前は config.json の roster_columns で変えられる（初期値は Luma の書き出しに合わせた名前）。

使い方
  python3 count_roster.py --event <フォルダ> --roster <名簿の CSV> [--delete]
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402

DEFAULT_COLUMNS = {"approval": "approval_status", "checked_in": "checked_in_at", "consent": "consent"}
YES = {"yes", "true", "1", "はい", "y"}


def update_register(base, event_id, counts):
    f = base / "register.csv"
    with open(f, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames
        rows = list(reader)
    for r in rows:
        if r["id"] == event_id:
            r.update({k: str(v) for k, v in counts.items()})
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description="名簿から件数だけを数える")
    p.add_argument("--event", required=True)
    p.add_argument("--roster", required=True)
    p.add_argument("--delete", action="store_true")
    a = p.parse_args()
    event = Path(a.event)
    base = lib.base_of_event(event)
    cols = dict(DEFAULT_COLUMNS, **(lib.load_json(base / "config.json", {}).get("roster_columns") or {}))
    with open(a.roster, encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        rows = list(reader)
    if cols["checked_in"] not in header:
        sys.stderr.write(f"名簿に来場の列（{cols['checked_in']}）がありません。config.json の roster_columns で列の名前を教えてください\n")
        return 2
    approved = [r for r in rows if cols["approval"] not in header or (r.get(cols["approval"]) or "").lower() == "approved"]
    counts = {
        "applied": len(approved),
        "attended": sum(1 for r in approved if (r.get(cols["checked_in"]) or "").strip()),
        "consented": sum(1 for r in approved if (r.get(cols["consent"]) or "").strip().lower() in YES) if cols["consent"] in header else "",
    }
    update_register(base, event.name, counts)
    line = f"- {lib.now_iso()[:10]} 申し込み {counts['applied']}・来場 {counts['attended']}・同意 {counts['consented'] if counts['consented'] != '' else '（列なし）'}"
    lib.append_to_section(event / "event-log.md", "当日の記録", line)
    lib.record_run(base, "middle", "verifier", "counted", None, applied=counts["applied"], attended=counts["attended"])
    if a.delete:
        Path(a.roster).unlink()
        print("名簿を消しました（件数だけ残した）")
    print(f"申し込み {counts['applied']}・来場 {counts['attended']}・同意 {counts['consented']}（register.csv に件数だけ書いた）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
