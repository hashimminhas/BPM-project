"""
LTAT.05.025 – Business Process Mining: CoatXR Project
Task 9: Effects of Change Activities

Analyses the impact of change activities (Change Quantity, Change Price,
Change Approval, etc.) on process efficiency and cycle time.

Authors: [Team names]
"""

import pandas as pd
import numpy as np
from collections import Counter

# ── Configuration ─────────────────────────────────────────────────────────────

DATA_PATH = "P2P_CoatXR_10_vendors.csv"

CHANGE_ACTIVITIES = [
    "Change Quantity",
    "Change Price",
    "Change Approval for Purchase Order",
    "Change Delivery Indicator",
    "Change Storage Location",
]

# ── Load and prepare data ─────────────────────────────────────────────────────

df = pd.read_csv(DATA_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values(["(case) Case Identifier", "timestamp"])

# Compute per-case cycle time (first to last event)
case_start = df.groupby("(case) Case Identifier")["timestamp"].min()
case_end   = df.groupby("(case) Case Identifier")["timestamp"].max()
cycle_time = (case_end - case_start).dt.total_seconds() / 86400  # in days

# Completed cases (last event = Clear Invoice or Record Goods Receipt)
case_last     = df.groupby("(case) Case Identifier")["label"].last()
completed_set = set(case_last[case_last.isin(["Clear Invoice", "Record Goods Receipt"])].index)

total_cases = df["(case) Case Identifier"].nunique()
print(f"Total cases: {total_cases:,}")

# ── Overview: frequency of each change activity ───────────────────────────────

print("\n── Change activity frequency ─────────────────────────────────")
for act in CHANGE_ACTIVITIES:
    n_events = (df["label"] == act).sum()
    n_cases  = df[df["label"] == act]["(case) Case Identifier"].nunique()
    print(f"  {act}")
    print(f"    Events: {n_events:,}  |  Cases: {n_cases:,}  ({n_cases/total_cases*100:.1f}%)")

# ── Baseline cycle time (cases with NO change activities) ─────────────────────

cases_with_any_change = set()
for act in CHANGE_ACTIVITIES:
    cases_with_any_change.update(
        df[df["label"] == act]["(case) Case Identifier"].unique()
    )

baseline_cases = set(cycle_time.index) - cases_with_any_change
baseline_ct    = cycle_time[list(baseline_cases)].median()

print(f"\n── Cycle time analysis ───────────────────────────────────────")
print(f"  Baseline (no change activities): {baseline_ct:.1f} days median  (n={len(baseline_cases):,})")

# ── Cycle time per change activity ────────────────────────────────────────────

for act in CHANGE_ACTIVITIES:
    act_cases  = set(df[df["label"] == act]["(case) Case Identifier"].unique())
    ct_all     = cycle_time[list(act_cases)].median()
    ct_comp    = cycle_time[list(act_cases & completed_set)].median()
    n_all      = len(act_cases)
    n_comp     = len(act_cases & completed_set)
    comp_rate  = n_comp / n_all * 100 if n_all else 0

    print(f"\n  {act}:")
    print(f"    Cases (all):            {n_all:,}  |  Median CT: {ct_all:.1f} days  ({ct_all - baseline_ct:+.1f} vs baseline)")
    print(f"    Cases (completed only): {n_comp:,} ({comp_rate:.1f}%)  |  Median CT: {ct_comp:.1f} days")

# ── Downstream effects: activities following each change event ────────────────

print("\n── Activities immediately following each change event ────────")
for act in CHANGE_ACTIVITIES:
    after = []
    for case_id, grp in df[df["(case) Case Identifier"].isin(
            df[df["label"] == act]["(case) Case Identifier"].unique()
        )].groupby("(case) Case Identifier"):
        acts = grp.sort_values("timestamp")["label"].tolist()
        for i, a in enumerate(acts):
            if a == act and i + 1 < len(acts):
                after.append(acts[i + 1])

    if not after:
        continue
    print(f"\n  After {act} ({len(after):,} events):")
    for next_act, count in Counter(after).most_common(6):
        print(f"    {count:5,}  {next_act}")

# ── Change Quantity: timing relative to Record Goods Receipt ──────────────────

print("\n── Change Quantity: does it occur before or after Goods Receipt? ──")

before_gr = 0
after_gr  = 0
no_gr     = 0

cq_cases = df[df["label"] == "Change Quantity"]["(case) Case Identifier"].unique()
for case_id, grp in df[df["(case) Case Identifier"].isin(cq_cases)].groupby("(case) Case Identifier"):
    acts = grp.sort_values("timestamp")["label"].tolist()
    if "Change Quantity" in acts and "Record Goods Receipt" in acts:
        cq_idx = acts.index("Change Quantity")
        gr_idx = acts.index("Record Goods Receipt")
        if cq_idx < gr_idx:
            before_gr += 1
        else:
            after_gr += 1
    else:
        no_gr += 1

total_cq = before_gr + after_gr + no_gr
print(f"  Change Quantity BEFORE Record GR: {before_gr:,} ({before_gr/total_cq*100:.1f}%)")
print(f"  Change Quantity AFTER  Record GR: {after_gr:,}  ({after_gr/total_cq*100:.1f}%)")
print(f"  Cases without Record GR:          {no_gr:,}   ({no_gr/total_cq*100:.1f}%)")

# ── Change Approval: overlap with Delete PO Item ──────────────────────────────

print("\n── Change Approval: overlap with Delete PO Item ─────────────")
approval_cases = set(df[df["label"] == "Change Approval for Purchase Order"]["(case) Case Identifier"].unique())
delete_cases   = set(df[df["label"] == "Delete Purchase Order Item"]["(case) Case Identifier"].unique())
overlap        = approval_cases & delete_cases
print(f"  Change Approval cases:                   {len(approval_cases):,}")
print(f"  Of those, ending in Delete PO Item:      {len(overlap):,} ({len(overlap)/len(approval_cases)*100:.1f}%)")

# ── Change Price: link to Remove Payment Block ────────────────────────────────

print("\n── Change Price: link to Remove Payment Block ────────────────")
price_cases = set(df[df["label"] == "Change Price"]["(case) Case Identifier"].unique())
rpb_cases   = set(df[df["label"] == "Remove Payment Block"]["(case) Case Identifier"].unique())
price_rpb   = price_cases & rpb_cases
print(f"  Change Price cases:                      {len(price_cases):,}")
print(f"  Of those, also have Remove Payment Block:{len(price_rpb):,} ({len(price_rpb)/len(price_cases)*100:.1f}%)")
