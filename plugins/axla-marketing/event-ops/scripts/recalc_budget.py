#!/usr/bin/env python3
"""収支の計算し直し（検証器・内側）。spec 003。手で計算しない。

入力（budget.json）
  {"venue": {"hourly": 13200, "hours": 3} または {"fixed": 39600},
   "fee": 2000, "fee_rate": 0.10, "per_person_cost": 0,
   "fixed_costs": [{"name": "料理", "amount": 0}], "capacity": 48,
   "headcounts": [20, 30, 40, 48], "currency": "円",
   "unverified": ["税込みかどうか", "準備と撤収の時間も料金がかかるか"]}

使い方
  python3 recalc_budget.py budget.json [--json]     # 表（Markdown）か JSON を出す
  python3 recalc_budget.py --event <イベントのフォルダ>
      → budget.md を作り直す。前回から変わったら event-log.md の「計画の変更」に1行書き、
        収支に関わる checklist の項目を未達に戻す。checklist の budget を達成にする
"""
import argparse
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402


def compute(b):
    venue = b.get("venue") or {}
    if "fixed" in venue:
        venue_total = Decimal(str(venue["fixed"]))
    else:
        venue_total = Decimal(str(venue.get("hourly", 0))) * Decimal(str(venue.get("hours", 0)))
    others = sum((Decimal(str(c.get("amount", 0))) for c in b.get("fixed_costs", [])), Decimal(0))
    fixed_total = venue_total + others
    fee = Decimal(str(b.get("fee", 0)))
    rate = Decimal(str(b.get("fee_rate", 0)))
    cost = Decimal(str(b.get("per_person_cost", 0)))
    margin = fee * (1 - rate) - cost
    breakeven = int(math.ceil(fixed_total / margin)) if margin > 0 else None
    capacity = b.get("capacity")
    within = breakeven if (breakeven is not None and (capacity is None or breakeven <= capacity)) else None
    heads = b.get("headcounts") or [h for h in (10, 20, 30, 40, 50) if capacity is None or h <= capacity]
    profit = {str(h): int(Decimal(h) * margin - fixed_total) for h in heads}
    return {
        "venue_total": int(venue_total),
        "fixed_total": int(fixed_total),
        "margin_per_person": float(margin),
        "breakeven": breakeven,
        "breakeven_within_capacity": within,
        "capacity": capacity,
        "profit": profit,
    }


def money(n, unit):
    sign = "+" if n > 0 else ("−" if n < 0 else "")
    return f"{sign}{abs(n):,} {unit}"


def markdown(b, r):
    unit = b.get("currency", "円")
    lines = ["| 人数 | 損益 |", "|---|---|"]
    for h, p in r["profit"].items():
        lines.append(f"| {h} | {money(p, unit)} |")
    if r["breakeven"] is None:
        be = "どの人数でも黒字にならない（1人あたりの粗利が 0 以下）"
    elif r["breakeven_within_capacity"] is None:
        be = f"定員 {r['capacity']} では届かない（{r['breakeven']} 人が要る）"
    else:
        be = f"{r['breakeven']} 人"
    out = [
        "# 収支（recalc_budget.py が作る。手で直さない）",
        "",
        f"- 赤字にならない人数：**{be}**",
        f"- 固定費：{r['fixed_total']:,} {unit}（会場 {r['venue_total']:,} {unit}）",
        f"- 1人あたりの粗利：{r['margin_per_person']:,.0f} {unit}（参加費 {b.get('fee', 0):,}・手数料 {float(b.get('fee_rate', 0)) * 100:.0f}%・原価 {b.get('per_person_cost', 0):,}）",
        "",
        *lines,
        "",
        "## 前提",
    ]
    for c in b.get("fixed_costs", []):
        out.append(f"- {c.get('name', '費用')}：{c.get('amount', 0):,} {unit}")
    for u in b.get("unverified", []):
        out.append(f"- 未確認：{u}")
    if not b.get("fixed_costs") and not b.get("unverified"):
        out.append("- （足した前提なし）")
    return "\n".join(out) + "\n"


def run_event(event_dir):
    event = Path(event_dir)
    b = lib.load_json(event / "budget.json")
    if b is None:
        sys.stderr.write(f"budget.json がありません：{event}\n")
        return 2
    r = compute(b)
    (event / "budget.md").write_text(markdown(b, r), encoding="utf-8")
    last = lib.load_json(event / "budget.last.json")
    base = lib.base_of_event(event)
    data = lib.load_checklist(event)
    changed = last is not None and (last.get("breakeven") != r["breakeven"] or last.get("fixed_total") != r["fixed_total"])
    if changed:
        old_be = last.get("breakeven") if last.get("breakeven") is not None else "なし"
        new_be = r["breakeven"] if r["breakeven"] is not None else "なし"
        line = f"- {lib.now_iso()[:10]} 赤字にならない人数 {old_be} → {new_be}（固定費 {last.get('fixed_total', 0):,} → {r['fixed_total']:,}）"
        lib.append_to_section(event / "event-log.md", "計画の変更", line)
        reset = []
        for item in data.get("items", []):
            if "budget" in item.get("depends_on", []) and item.get("passes"):
                item["passes"], item["evidence"] = False, None
                reset.append(item["id"])
        if reset:
            print("収支が変わったので未達に戻した項目：" + "、".join(reset))
    for item in data.get("items", []):
        if item["id"] == "budget":
            item["passes"], item["evidence"] = True, "budget.md"
    lib.save_json(lib.checklist_path(event), data)
    lib.save_json(event / "budget.last.json", r)
    lib.record_run(base, "inner", "verifier", "recalculated", None, item="budget", changed=bool(changed))
    print(f"赤字にならない人数：{r['breakeven'] if r['breakeven'] is not None else 'なし'}（budget.md を作り直した）")
    return 0


def main():
    p = argparse.ArgumentParser(description="収支の計算し直し")
    p.add_argument("budget", nargs="?")
    p.add_argument("--json", action="store_true")
    p.add_argument("--event")
    a = p.parse_args()
    if a.event:
        return run_event(a.event)
    if not a.budget:
        p.error("budget.json か --event を指定してください")
    b = lib.load_json(a.budget)
    if b is None:
        sys.stderr.write("budget.json が読めません\n")
        return 2
    r = compute(b)
    print(json.dumps(r, ensure_ascii=False) if a.json else markdown(b, r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
