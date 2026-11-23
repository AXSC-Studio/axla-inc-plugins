#!/usr/bin/env python3
"""告知の下書きを作る（内側）。spec 004。

events/<ID>/event.json（イベントの事実）から、次の2つを kit/ に作る。
- event_page.md   … 告知サービスに貼る文面（manual のときはこれを人が貼る）
- event_page.json … 告知サービスに渡す中身（luma のときは公式 MCP の作成の道具にこの値を渡す）

守ること（コードで守る）
- 公開の設定はいつも private。公開は、人のまとめ承認のあと（spec 002 の hook が止める）
- 定員・参加費が budget.json と食い違えば exit 1（資料の数は計画と一致させる）
- 日付・開始・終了・題・場所が無ければ exit 1

使い方
  python3 event_page.py --event <イベントのフォルダ>
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402

REQUIRED = ["title", "date", "start", "end", "timezone", "place_area"]


def iso(date, hm, tz):
    dt = datetime.strptime(f"{date} {hm}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(tz))
    return dt.isoformat()


def main():
    p = argparse.ArgumentParser(description="告知の下書きを作る")
    p.add_argument("--event", required=True)
    a = p.parse_args()
    event = Path(a.event)
    facts = lib.load_json(event / "event.json")
    if facts is None:
        sys.stderr.write("event.json がありません\n")
        return 2
    budget = lib.load_json(event / "budget.json", {})
    problems = [f"{k} が無い" for k in REQUIRED if not facts.get(k)]
    capacity = facts.get("capacity", budget.get("capacity"))
    fee = facts.get("fee", budget.get("fee"))
    if budget.get("capacity") is not None and capacity != budget.get("capacity"):
        problems.append(f"定員が計画と違う（告知 {capacity}・budget.json {budget.get('capacity')}）")
    if budget.get("fee") is not None and fee != budget.get("fee"):
        problems.append(f"参加費が計画と違う（告知 {fee}・budget.json {budget.get('fee')}）")
    if facts.get("start") and not re.fullmatch(r"\d{2}:\d{2}", str(facts["start"])):
        problems.append("start は HH:MM で")
    if problems:
        print("告知の下書きを作れません：")
        for x in problems:
            print("  " + x)
        lib.record_run(lib.base_of_event(event), "inner", "verifier", "failed", "event_page_facts", count=len(problems))
        return 1

    tz = facts["timezone"]
    unit = budget.get("currency", "円")
    if str(facts.get("visibility", "private")).lower() != "private":
        print("visibility は private にしました（公開は、人のまとめ承認のあと）")
    payload = {
        "name": facts["title"],
        "start_at": iso(facts["date"], facts["start"], tz),
        "end_at": iso(facts["date"], facts["end"], tz),
        "timezone": tz,
        "max_capacity": capacity,
        "visibility": "private",
        "description_md": "",
        "ticket": {"type": "paid" if fee else "free", "amount": fee or 0, "currency": unit},
        "location_note": facts["place_area"],
    }
    points = "\n".join(f"- {x}" for x in facts.get("points", []))
    description = "\n".join(filter(None, [
        points,
        f"\n**こんな人に**：{facts['audience']}" if facts.get("audience") else "",
        f"\n**参加費**：{fee:,} {unit}" if fee else "\n**参加費**：無料",
        f"**定員**：{capacity} 名" if capacity else "",
    ]))
    payload["description_md"] = description
    md = "\n".join([
        f"# {facts['title']}",
        "",
        f"- 日時：{facts['date']} {facts['start']}〜{facts['end']}（{tz}）",
        f"- 場所：{facts['place_area']}",
        f"- 参加費：{fee:,} {unit}" if fee else "- 参加費：無料",
        f"- 定員：{capacity} 名" if capacity else "- 定員：未定【G1】",
        "- 公開：非公開の下書き（公開は人のまとめ承認のあと）",
        "",
        "## 説明",
        description,
        "",
    ])
    (event / "kit").mkdir(exist_ok=True)
    (event / "kit" / "event_page.md").write_text(md, encoding="utf-8")
    lib.save_json(event / "kit" / "event_page.json", payload)
    lib.record_run(lib.base_of_event(event), "inner", "verifier", "passed", None, item="event_page")
    print("kit/event_page.md と kit/event_page.json を作りました（visibility: private）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
