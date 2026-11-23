#!/usr/bin/env python3
"""内側のループの検証器。spec 003。

exit 0：checklist の全項目が達成で、証拠がそろっている
exit 1：未達がある／証拠が崩れている／会場の確定（G2）のあとに【仮】が残っている
exit 2：checklist.json が無い

使い方
  python3 check_kit.py --event <イベントのフォルダ>
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eventops_lib as lib  # noqa: E402

TENTATIVE = "【仮】"
SCAN_SUFFIXES = {".md", ".txt", ".json", ".html", ".csv"}


def tentative_left(event):
    hits = []
    for p in sorted(event.rglob("*")):
        if not p.is_file() or p.suffix not in SCAN_SUFFIXES:
            continue
        rel = p.relative_to(event)
        if rel.parts[0] in ("reviews", "approvals", "sent") or p.name in ("event-log.md", "checklist.json", "state.json"):
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if TENTATIVE in line:
                hits.append(f"{rel}:{n}")
    return hits


def main():
    p = argparse.ArgumentParser(description="内側のループの検証器")
    p.add_argument("--event", required=True)
    a = p.parse_args()
    event = Path(a.event)
    if not lib.checklist_path(event).exists():
        sys.stderr.write("checklist.json がありません。new_event.py init で作ってください\n")
        return 2
    problems = [f"{iid}：{why}" for iid, why in lib.unmet_items(event)]
    st = lib.load_json(event / "state.json", {})
    if st.get("g2_confirmed"):
        problems += [f"会場の確定のあとに【仮】が残っている：{h}" for h in tentative_left(event)]
    base = lib.base_of_event(event)
    if problems:
        print("内側はまだ終わっていません：")
        for x in problems:
            print("  " + x)
        lib.record_run(base, "inner", "verifier", "failed", "kit_unmet", count=len(problems))
        return 1
    lib.record_run(base, "inner", "verifier", "passed", None, item="kit")
    print("内側は完了：checklist の全項目が達成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
