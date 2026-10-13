#!/usr/bin/env python3
"""Pull the headline numbers out of a Vivado build directory into one line.

    python3 scripts/synth_report.py vivado_cpu
    vivado_cpu: 608 LUTs (88 as distributed RAM), 30 FFs | clk 10.000 ns: WNS +0.505 ns, WHS +0.231 ns, met (~105 MHz)

Reads utilization.rpt and, if present, timing_summary.rpt. Exits 1 if timing
was analysed and failed, or with --require-timing if there is no timing data
at all, so a Make target can stop on a bad build.
"""
import argparse
import re
import sys
from pathlib import Path


def table_value(text, row):
    """First number after `| <row> |` in a Vivado utilization table."""
    m = re.search(r"^\|\s*" + re.escape(row) + r"\s*\|\s*(\d+)", text, re.MULTILINE)
    return int(m.group(1)) if m else None


def parse_utilization(path):
    text = path.read_text()
    return {
        "luts": table_value(text, "Slice LUTs"),
        "lutram": table_value(text, "LUT as Distributed RAM"),
        "ffs": table_value(text, "Slice Registers"),
    }


def parse_timing(path):
    """WNS/WHS from the Design Timing Summary, period of the first clock.

    WNS is "NA" when nothing is constrained (e.g. a register file with no
    reg-to-reg paths); that comes back as None rather than a fake number.
    """
    text = path.read_text()
    m = re.search(r"WNS\(ns\).*?\n\s*-+.*?\n\s*(\S+)\s+\S+\s+\S+\s+\S+\s+(\S+)", text)
    if not m:
        return None
    to_float = lambda s: None if s == "NA" else float(s)
    period = re.search(r"Clock\s+Waveform\(ns\)\s+Period\(ns\).*?\n-+.*?\n(\S+)\s+\{[^}]*\}\s+(\S+)", text)
    return {
        "wns": to_float(m.group(1)),
        "whs": to_float(m.group(2)),
        "clock": period.group(1) if period else None,
        "period": float(period.group(2)) if period else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("build_dir", type=Path, help="Vivado output dir, e.g. vivado_cpu")
    ap.add_argument("--require-timing", action="store_true",
                    help="fail if there is no timing data to check")
    args = ap.parse_args()

    util_path = args.build_dir / "utilization.rpt"
    if not util_path.exists():
        sys.exit(f"{util_path} not found: run the Vivado build first")
    u = parse_utilization(util_path)
    line = f"{args.build_dir.name}: {u['luts']} LUTs ({u['lutram']} as distributed RAM), {u['ffs']} FFs"

    t = None
    timing_path = args.build_dir / "timing_summary.rpt"
    if timing_path.exists():
        t = parse_timing(timing_path)

    failed = False
    if t is None or t["wns"] is None:
        line += " | timing: not analysed (no constrained paths)"
        failed = args.require_timing
    else:
        met = t["wns"] >= 0 and (t["whs"] is None or t["whs"] >= 0)
        line += f" | {t['clock']} {t['period']:.3f} ns: WNS {t['wns']:+.3f} ns"
        if t["whs"] is not None:
            line += f", WHS {t['whs']:+.3f} ns"
        line += ", met" if met else ", FAILED"
        if t["period"]:
            line += f" (~{1000 / (t['period'] - t['wns']):.0f} MHz)"
        failed = not met

    print(line)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
