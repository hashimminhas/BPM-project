"""
Tasks 5, 6 & 7 — CoatXR Process Mining (LTAT.05.025)

Run in Cursor:
  1. Open this file
  2. Terminal: pip install -r requirements.txt   (first time only)
  3. Right-click → "Run Python File"  OR  terminal: python tasks_5_6_7.py

Outputs: printed tables + PNG charts in outputs/
"""

from __future__ import annotations

import warnings
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 120

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)

MILESTONES = [
    "Create Purchase Order Item",
    "Record Goods Receipt",
    "Vendor creates invoice",
    "Record Invoice Receipt",
    "Clear Invoice",
]

PHASE_COLS = [
    "P0_pre_PO_days",
    "P1_PO_to_parallel_days",
    "P2_parallel_to_record_inv_days",
    "P3_record_to_clear_days",
]
PHASE_LABELS = ["P0 Pre-PO", "P1 PO->parallel", "P2->Record inv.", "P3->Clear"]


def load_events() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "P2P_CoatXR_10_vendors.csv.gz", compression="gzip")
    df.columns = [c.strip().replace("(case) ", "").replace("lifecycle:", "") for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values(["Case Identifier", "timestamp"])


def milestone_times(group: pd.DataFrame) -> dict | None:
    out = {}
    for m in MILESTONES:
        ts = group.loc[group["label"] == m, "timestamp"]
        if ts.empty:
            return None
        out[m] = {"first": ts.iloc[0], "last": ts.iloc[-1]}
    return out


def days_between(a: pd.Timestamp, b: pd.Timestamp) -> float:
    return max(0.0, (b - a).total_seconds() / 86400)


def extract_loops(activities: list[str]) -> list[tuple[str, ...]]:
    loops = []
    first_idx: dict[str, int] = {}
    for i, act in enumerate(activities):
        if act in first_idx:
            loop = tuple(activities[first_idx[act] : i + 1])
            if len(loop) >= 2:
                loops.append(loop)
        else:
            first_idx[act] = i
    return loops


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    cases = pd.read_csv(ROOT / "coatxr_cases_shared.csv", parse_dates=["start_time", "end_time"])
    events = load_events()

    section("SETUP")
    print(f"Cases: {len(cases):,} | Events: {len(events):,}")
    print(f"Log: {events['timestamp'].min()} -> {events['timestamp'].max()}")
    print(f"Completed: {(cases['Status'] == 'Completed').sum():,}")
    print(f"Ongoing:   {(cases['Status'] == 'Ongoing').sum():,}")

    # ── TASK 5 ────────────────────────────────────────────────────────────────
    section("TASK 5 - Process milestones & phases")
    print(
        "Completed cases only. Phases (parallel-aware):\n"
        "  P0: start -> first Create PO\n"
        "  P1: last Create PO -> max(last GR, last vendor invoice)\n"
        "  P2: parallel end -> last Record Invoice Receipt\n"
        "  P3: last Record Invoice Receipt -> last Clear Invoice\n"
    )

    completed_ids = set(cases.loc[cases["Status"] == "Completed", "Case Identifier"])
    ev = events[events["Case Identifier"].isin(completed_ids)]

    rows = []
    skipped = 0
    for cid, g in ev.groupby("Case Identifier"):
        mt = milestone_times(g)
        if mt is None:
            skipped += 1
            continue
        start = g["timestamp"].iloc[0]
        po, gr, vi, ri, cl = (mt[m] for m in MILESTONES)
        parallel_end = max(gr["last"], vi["last"])
        rows.append(
            {
                "Case Identifier": cid,
                "P0_pre_PO_days": days_between(start, po["first"]),
                "P1_PO_to_parallel_days": days_between(po["last"], parallel_end),
                "P2_parallel_to_record_inv_days": days_between(parallel_end, ri["last"]),
                "P3_record_to_clear_days": days_between(ri["last"], cl["last"]),
            }
        )

    phases = pd.DataFrame(rows).merge(cases, on="Case Identifier", how="left")
    print(f"\nCases with all 5 milestones: {len(phases):,} (skipped {skipped:,})")
    print("\nMedian phase duration (days):")
    print(phases[PHASE_COLS].median().round(2).to_string())

    print("\nMilestone rework (cases with >1 occurrence):")
    for m in MILESTONES:
        n = int((ev[ev["label"] == m].groupby("Case Identifier").size() > 1).sum())
        print(f"  {m}: {n:,}")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    medians = phases[PHASE_COLS].median()
    axes[0].barh(PHASE_LABELS, medians, color=["#90CAF9", "#42A5F5", "#1E88E5", "#0D47A1"])
    axes[0].set_xlabel("Median days")
    axes[0].set_title("Task 5 - Phase medians")
    axes[1].boxplot([phases[c] for c in PHASE_COLS], tick_labels=PHASE_LABELS)
    axes[1].set_ylabel("Days")
    axes[1].set_title("Phase distributions")
    plt.tight_layout()
    p5 = OUT_DIR / "task5_phases.png"
    plt.savefig(p5, bbox_inches="tight")
    plt.close()
    print(f"\nSaved: {p5}")

    # ── TASK 6 ────────────────────────────────────────────────────────────────
    section("TASK 6 - WiP & seasonality")

    cases = cases.copy()
    cases["start_month"] = cases["start_time"].dt.to_period("M").dt.to_timestamp()
    cases["end_month"] = cases["end_time"].dt.to_period("M").dt.to_timestamp()
    months = pd.date_range(
        cases["start_time"].min().normalize(),
        cases["end_time"].max().normalize(),
        freq="MS",
    )

    wip_rows = []
    for t in months:
        active = (cases["start_time"] <= t) & (cases["end_time"] > t)
        wip_rows.append(
            {
                "month": t,
                "wip": int(active.sum()),
                "arrivals": int((cases["start_month"] == t).sum()),
                "departures": int((cases["end_month"] == t).sum()),
            }
        )
    wip = pd.DataFrame(wip_rows)
    wip["month"] = wip["month"].dt.strftime("%Y-%m")
    wip_csv = OUT_DIR / "task6_wip_monthly.csv"
    wip.to_csv(wip_csv, index=False)

    events = events.copy()
    events["month"] = events["timestamp"].dt.to_period("M").dt.to_timestamp()
    monthly_events = events.groupby("month").size().reset_index(name="event_count")
    monthly_events["month"] = monthly_events["month"].dt.strftime("%Y-%m")
    monthly_events.to_csv(OUT_DIR / "task6_events_per_month.csv", index=False)

    print(wip.to_string(index=False))
    print(f"\nSaved data: {wip_csv}")
    peak = wip.loc[wip["wip"].idxmax()]
    print(f"\nPeak WiP: {int(peak['wip']):,} in {peak['month']}")

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    axes[0, 0].plot(wip["month"], wip["wip"], "o-", color="#1565C0")
    axes[0, 0].set_title("Work in Progress over time")
    axes[0, 0].tick_params(axis="x", rotation=45)
    x = np.arange(len(wip))
    axes[0, 1].bar(x - 10, wip["arrivals"], width=20, label="Starts", color="#66BB6A")
    axes[0, 1].bar(x + 10, wip["departures"], width=20, label="Ends", color="#EF5350")
    axes[0, 1].legend()
    axes[0, 1].set_title("Arrivals vs departures")
    events.groupby("month").size().plot(kind="bar", ax=axes[1, 0], color="#7E57C2")
    axes[1, 0].set_title("Events per month")
    axes[1, 0].tick_params(axis="x", rotation=45)
    dow = events["timestamp"].dt.dayofweek.value_counts().sort_index()
    axes[1, 1].bar(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], dow.values)
    axes[1, 1].set_title("Events by weekday")
    plt.tight_layout()
    p6 = OUT_DIR / "task6_wip_seasonality.png"
    plt.savefig(p6, bbox_inches="tight")
    plt.close()
    print(f"Saved: {p6}")

    # ── TASK 7 ────────────────────────────────────────────────────────────────
    section("TASK 7 - Rework loops")

    loop_counter: Counter = Counter()
    case_loops: dict[tuple[str, ...], set] = {}
    for cid, g in events.groupby("Case Identifier"):
        for loop in extract_loops(g["label"].tolist()):
            loop_counter[loop] += 1
            case_loops.setdefault(loop, set()).add(cid)

    top3 = loop_counter.most_common(3)
    ct = cases.set_index("Case Identifier")["cycle_time_days"]
    impact_rows = []
    for i, (loop, cnt) in enumerate(top3, 1):
        with_l = case_loops[loop]
        without = set(ct.index) - with_l
        med_with = ct.loc[list(with_l)].median()
        med_without = ct.loc[list(without)].median()
        impact_rows.append(
            {
                "loop": " -> ".join(loop),
                "cases": cnt,
                "median_with": round(med_with, 1),
                "median_without": round(med_without, 1),
                "delta_days": round(med_with - med_without, 1),
            }
        )
        print(f"\nLoop {i} ({cnt:,} cases): {' -> '.join(loop)}")
        print(f"  Median cycle time WITH: {med_with:.1f} d | WITHOUT: {med_without:.1f} d | delta: {med_with - med_without:+.1f} d")

    impact_df = pd.DataFrame(impact_rows)

    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(3)
    ax.bar(x - 0.2, impact_df["median_without"], width=0.4, label="Without loop")
    ax.bar(x + 0.2, impact_df["median_with"], width=0.4, label="With loop", color="#E53935")
    ax.set_xticks(x)
    ax.set_xticklabels(["Loop 1", "Loop 2", "Loop 3"])
    ax.set_ylabel("Median cycle time (days)")
    ax.legend()
    ax.set_title("Task 7 - Cycle time impact")
    plt.tight_layout()
    p7 = OUT_DIR / "task7_rework_impact.png"
    plt.savefig(p7, bbox_inches="tight")
    plt.close()
    print(f"\nSaved: {p7}")

    any_rework = events.groupby("Case Identifier")["label"].apply(lambda s: s.duplicated().any())
    print(
        f"\nCases with any repeated activity: {any_rework.sum():,} "
        f"({any_rework.mean() * 100:.1f}%)"
    )

    section("DONE")
    print("Use printed numbers + PNG files in outputs/ for your report.")
    print("Open outputs/ in Cursor sidebar to view charts.")


if __name__ == "__main__":
    main()
