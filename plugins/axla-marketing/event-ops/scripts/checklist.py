#!/usr/bin/env python3
"""内側のループの台帳（checklist.json）を動かす道具。spec 003。

規則（コードで守る）
- 項目は全部「未達」から始まる
- 証拠のファイルが無い項目は「達成」にできない
- 検証役（kind: review）の項目は、証拠に「致命的: 0」が無ければ達成にできない
- 検証役の項目は、スクリプト（kind: script）の項目が全部達成になってからでないと達成にできない
- start で内側のループを始めると、Stop hook（hooks/stop_guard.py）が未達のあいだ止めさせない

使い方
  python3 checklist.py start  --event <フォルダ>                 # 内側のループを始める（周を 0 に）
  python3 checklist.py mark   --event <フォルダ> --item ID --evidence <パスか URL>
  python3 checklist.py reset  --event <フォルダ> --because budget  # その前提に関わる項目を未達に戻す
  python3 checklist.py status --event <フォルダ>                 # 未達があれば exit 1
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402


def cmd_start(a):
    event = Path(a.event)
    st = lib.load_json(event / "state.json", {})
    st["inner_active"] = True
    st["round"] = 0
    lib.save_json(event / "state.json", st)
    lib.record_run(lib.base_of_event(event), "inner", "trigger", "started")
    print("内側のループを始めました。未達が残るあいだ、Stop hook が止めさせません（上限 %s 周）" % st.get("max_rounds", 3))
    return 0


def cmd_mark(a):
    event = Path(a.event)
    data = lib.load_checklist(event)
    item = next((i for i in data.get("items", []) if i["id"] == a.item), None)
    if item is None:
        sys.stderr.write(f"項目 {a.item} はありません\n")
        return 2
    if item.get("kind") == "review":
        scripts_unmet = [i["id"] for i in data["items"] if i.get("kind") == "script" and (not i.get("passes") or lib.evidence_problem(event, i))]
        if scripts_unmet:
            print(f"検証役の項目は、スクリプトの項目（{'、'.join(scripts_unmet)}）が達成になってからです")
            return 1
    trial = dict(item, evidence=a.evidence)
    why = lib.evidence_problem(event, trial)
    if why:
        print(f"{a.item} は達成にできません：{why}")
        lib.record_run(lib.base_of_event(event), "inner", "verifier", "rejected", "bad_evidence", item=a.item)
        return 1
    item["passes"], item["evidence"] = True, a.evidence
    lib.save_json(lib.checklist_path(event), data)
    lib.record_run(lib.base_of_event(event), "inner", "verifier", "passed", None, item=a.item)
    left = lib.unmet_items(event)
    print(f"{a.item} を達成にしました（残り {len(left)} 件）")
    return 0


def cmd_reset(a):
    event = Path(a.event)
    data = lib.load_checklist(event)
    reset = []
    for i in data.get("items", []):
        if a.because in i.get("depends_on", []) and i.get("passes"):
            i["passes"], i["evidence"] = False, None
            reset.append(i["id"])
    lib.save_json(lib.checklist_path(event), data)
    print("未達に戻した項目：" + ("、".join(reset) if reset else "なし"))
    return 0


def cmd_status(a):
    left = lib.unmet_items(Path(a.event))
    if left:
        print(f"未達 {len(left)} 件：")
        for iid, why in left:
            print(f"  {iid}：{why}")
        return 1
    print("全部達成")
    return 0


def main():
    p = argparse.ArgumentParser(description="内側のループの台帳")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("start", "mark", "reset", "status"):
        s = sub.add_parser(name)
        s.add_argument("--event", required=True)
        if name == "mark":
            s.add_argument("--item", required=True)
            s.add_argument("--evidence", required=True)
        if name == "reset":
            s.add_argument("--because", required=True)
    a = p.parse_args()
    return {"start": cmd_start, "mark": cmd_mark, "reset": cmd_reset, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
