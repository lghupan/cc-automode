#!/usr/bin/env python3
"""
report.py — Compare results across containers and print a side-by-side table

Usage:
  python3 report.py <custom.json> <official.json> [yolo.json]
  python3 report.py results/custom/custom.json results/official/official.json results/yolo/yolo.json
"""

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------

RESET  = "\x1b[0m"
GREEN  = "\x1b[32m"
RED    = "\x1b[31m"
YELLOW = "\x1b[33m"
BOLD   = "\x1b[1m"
DIM    = "\x1b[2m"
CYAN   = "\x1b[36m"

def c(text, code):
    return f"{code}{text}{RESET}"

def strip_ansi(s):
    return re.sub(r"\x1b\[[0-9;]*m", "", s)

def pad(s, width):
    return s + " " * max(0, width - len(strip_ansi(s)))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load(path):
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None

def get_result(data, id_):
    if not data:
        return None
    return next((r for r in data.get("results", []) if r["id"] == id_), None)

def decision_cell(decision, expected, width=16):
    if decision is None:
        return pad(c("N/A", DIM), width)
    correct = decision == expected
    icon = "✓" if correct else "✗"
    col = GREEN if correct else RED
    return pad(c(f"{icon} {decision}", col), width)

def score_str(passed, total):
    if total == 0:
        return "N/A"
    pct = round(passed / total * 100)
    col = GREEN if pct == 100 else YELLOW if pct >= 75 else RED
    return c(f"{passed}/{total} ({pct}%)", col)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    custom   = load(args[0] if len(args) > 0 else None)
    official = load(args[1] if len(args) > 1 else None)
    yolo     = load(args[2] if len(args) > 2 else None)

    if not custom and not official and not yolo:
        print("No result files found. Run compare.sh first.", file=sys.stderr)
        sys.exit(1)

    cases = json.loads((Path(__file__).parent / "cases.json").read_text())

    # Header
    ts = (custom or official or yolo or {}).get("timestamp", "")
    print()
    print(c("═" * 110, BOLD))
    print(c(" Claude Code Auto Mode — Benchmark Report", BOLD) + (c(f"  ({ts})", DIM) if ts else ""))
    print(c("═" * 110, BOLD))
    print()
    print(c("A  cc-automode     classifier.py hook  [--dangerously-skip-permissions]", CYAN))
    print(c("B  Auto mode       internal classifier  [--permission-mode auto]", CYAN))
    print(c("C  YOLO mode   no hooks, no CLAUDE.md  [--dangerously-skip-permissions]", CYAN))
    print()

    # Table
    COL_ID, COL_NAME, COL_EXP, COL_C = 8, 38, 10, 16

    header_cols = [
        pad(c("ID",           BOLD), COL_ID),
        pad(c("Test Case",    BOLD), COL_NAME),
        pad(c("Expected",     BOLD), COL_EXP),
        pad(c("A cc-automode",BOLD), COL_C),
        pad(c("B Auto mode",  BOLD), COL_C),
    ]
    if yolo:
        header_cols.append(pad(c("C YOLO mode", BOLD), COL_C))
    print("  ".join(header_cols))
    print(c("─" * 110, DIM))

    pos = {"custom": [0,0], "official": [0,0], "yolo": [0,0]}
    neg = {"custom": [0,0], "official": [0,0], "yolo": [0,0]}

    for tc in cases:
        ca = get_result(custom,   tc["id"])
        co = get_result(official, tc["id"])
        cy = get_result(yolo,     tc["id"])

        a_dec = ca["decision"] if ca else None
        b_dec = co["decision"] if co else None
        c_dec = cy["decision"] if cy else None

        row = [
            pad(c(tc["id"], DIM), COL_ID),
            pad(tc["name"][:COL_NAME - 2], COL_NAME),
            pad(c(tc["expected"], GREEN if tc["expected"] == "ALLOW" else RED), COL_EXP),
            decision_cell(a_dec, tc["expected"], COL_C),
            decision_cell(b_dec, tc["expected"], COL_C),
        ]
        if yolo:
            row.append(decision_cell(c_dec, tc["expected"], COL_C))
        print("  ".join(row))

        bucket = pos if tc["category"] == "positive" else neg
        for key, dec in [("custom", a_dec), ("official", b_dec), ("yolo", c_dec)]:
            if dec is not None:
                bucket[key][1] += 1
                if dec == tc["expected"]:
                    bucket[key][0] += 1

    print(c("─" * 110, DIM))

    # Summary
    print(f"\n{c('Summary', BOLD)}\n")
    headers = ["", "A  cc-automode", "B  Auto mode"]
    if yolo:
        headers.append("C  YOLO mode")

    rows = [
        headers,
        ["Positive (should ALLOW)",
            score_str(*pos["custom"]), score_str(*pos["official"])]
            + ([score_str(*pos["yolo"])] if yolo else []),
        ["Negative (should BLOCK)",
            score_str(*neg["custom"]), score_str(*neg["official"])]
            + ([score_str(*neg["yolo"])] if yolo else []),
        ["Overall",
            score_str(custom["passed"],   custom["total"])   if custom   else "N/A",
            score_str(official["passed"], official["total"]) if official else "N/A"]
            + ([score_str(yolo["passed"], yolo["total"]) if yolo else "N/A"] if yolo else []),
    ]
    for row in rows:
        line = "  " + pad(row[0], 28)
        for cell in row[1:]:
            line += pad(cell, 26)
        print(line)

    # Discrepancies between A and B
    discrepancies = [
        tc for tc in cases
        if (r_a := get_result(custom, tc["id"])) and (r_b := get_result(official, tc["id"]))
        and r_a["decision"] != r_b["decision"]
    ]
    if discrepancies:
        n = len(discrepancies)
        print(f"\n{c(f'⚠  {n} discrepanc{\"y\" if n == 1 else \"ies\"} between A and B:', YELLOW)}")
        for tc in discrepancies:
            ca = get_result(custom, tc["id"])
            co = get_result(official, tc["id"])
            a_wrong = ca["decision"] != tc["expected"]
            b_wrong = co["decision"] != tc["expected"]
            print(f"\n  [{tc['id']}] {tc['name']}")
            print(f"    Expected: {tc['expected']}")
            print(f"    A: {c(ca['decision'], RED if a_wrong else GREEN)} {'(incorrect)' if a_wrong else '(correct)'}")
            print(f"    B: {c(co['decision'], RED if b_wrong else GREEN)} {'(incorrect)' if b_wrong else '(correct)'}")
            print(f"    Rule: {tc['rule']}")
    elif custom and official:
        print(f"\n{c('✓  A and B agree on all cases.', GREEN)}")

    print("\n" + c("═" * 110, BOLD) + "\n")


if __name__ == "__main__":
    main()
