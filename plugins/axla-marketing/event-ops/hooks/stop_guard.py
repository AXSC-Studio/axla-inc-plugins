#!/usr/bin/env python3
"""内側のループの終了条件（Exit Criteria）と予算上限（Budget Cap）。spec 003。

Claude Code の Stop hook。Claude が「終わった」と言おうとするたびに動く。
- 内側のループ（checklist.py start で始めたもの）が動いていなければ、何もしない
- checklist の全項目が達成なら、止めてよい（達成）。ループを閉じる
- 未達があり、周が上限（max_rounds、初期値 3）に届いていなければ、止めさせずにもう1周（block）
- 上限に届いたら、G1（人の判断）に上げて止めてよい（人へ）

終わり方は3つだけ：達成・人へ・予算切れ（上限）。どれも runs.jsonl に1行残す。
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import eventops_lib as lib  # noqa: E402


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())
    base = project / lib.DATA_DIR
    if not base.is_dir():
        return 0
    for state_file in sorted(base.glob("events/*/state.json")):
        st = lib.load_json(state_file, {})
        if not st.get("inner_active"):
            continue
        event = state_file.parent
        left = lib.unmet_items(event)
        max_rounds = int(st.get("max_rounds", 3))
        if not left:
            st["inner_active"] = False
            lib.save_json(state_file, st)
            lib.record_run(base, "inner", "exit_criteria", "achieved", None, event=event.name, rounds=st.get("round", 0))
            continue
        if st.get("round", 0) >= max_rounds:
            st["inner_active"] = False
            lib.save_json(state_file, st)
            ids = "、".join(i for i, _ in left)
            lib.append_to_section(event / "event-log.md", "開いている人の判断",
                                  f"- {lib.now_iso()[:10]} G1：内側が {max_rounds} 周で終わらない。未達：{ids}。どう直すか、何を諦めるかを決めてください")
            lib.record_run(base, "inner", "budget_cap", "escalated", "max_rounds", event=event.name, unmet=len(left))
            continue
        st["round"] = st.get("round", 0) + 1
        lib.save_json(state_file, st)
        lib.record_run(base, "inner", "exit_criteria", "continued", "unmet", event=event.name, round=st["round"], unmet=len(left))
        detail = "；".join(f"{i}（{why}）" for i, why in left[:8])
        reason = (
            f"[event-ops 内側のループ {event.name}] 周 {st['round']}/{max_rounds}：未達が {len(left)} 件あります。"
            f"{detail}。直して、checklist.py mark で証拠を付け、check_kit.py が exit 0 になってから終えてください。"
            f"{max_rounds} 周で終わらなければ G1 に上げて止まります。"
        )
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
