"""
LTAT.05.025 – Business Process Mining: CoatXR Project
Task 8: Effects of Cancellations and Deletions

Analyses over-processing caused by cancelled/deleted purchase order items,
cancelled invoice receipts, and cancelled goods receipts.

Authors: [Team names]
"""

import pandas as pd
import numpy as np
from collections import Counter

# ── Configuration ─────────────────────────────────────────────────────────────

DATA_PATH = "P2P_CoatXR_10_vendors.csv"

CANCELLATION_ACTIVITIES = [
    "Cancel Goods Receipt",
    "Cancel Invoice Receipt",
    "Delete Purchase Order Item",
    "Reactivate Purchase Order Item",
]

# ── Load and prepare data ─────────────────────────────────────────────────────

df = pd.read_csv(DATA_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values(["(case) Case Identifier", "timestamp"])

total_cases = df["(case) Case Identifier"].nunique()
print(f"Total cases in log: {total_cases}")

# ── Overview: how many cases are affected by each cancellation activity ───────

print("\n── Cancellation/deletion activity overview ──────────────────")
for act in CANCELLATION_ACTIVITIES:
    n_events = (df["label"] == act).sum()
    n_cases  = df[df["label"] == act]["(case) Case Identifier"].nunique()
    print(f"  {act}")
    print(f"    Events: {n_events:,}  |  Cases affected: {n_cases:,}  ({n_cases/total_cases*100:.1f}%)")

# ── Delete Purchase Order Item: over-processing analysis ─────────────────────

print("\n── Delete Purchase Order Item: over-processing ───────────────")

del_cases = df[df["label"] == "Delete Purchase Order Item"]["(case) Case Identifier"].unique()
del_df    = df[df["(case) Case Identifier"].isin(del_cases)]

# Activities executed BEFORE the Delete PO event in each case
wasted_activity_counts = []
all_wasted_activities  = []

for case_id, grp in del_df.groupby("(case) Case Identifier"):
    acts = grp.sort_values("timestamp")["label"].tolist()
    try:
        del_idx = acts.index("Delete Purchase Order Item")
        before  = acts[:del_idx]
        wasted_activity_counts.append(len(before))
        all_wasted_activities.extend(before)
    except ValueError:
        pass

print(f"  Cases with Delete PO Item:              {len(del_cases):,}")
print(f"  Total wasted activity executions:       {sum(wasted_activity_counts):,}")
print(f"  Mean activities wasted per case:        {np.mean(wasted_activity_counts):.1f}")
print(f"  Median activities wasted per case:      {np.median(wasted_activity_counts):.1f}")

print("\n  Breakdown of wasted activities:")
for act, count in Counter(all_wasted_activities).most_common():
    print(f"    {count:5,}  {act}")

# Time from Create PO Item to Delete PO Item (over-processing duration)
create_ts = df[df["label"] == "Create Purchase Order Item"].groupby(
    "(case) Case Identifier")["timestamp"].first()
delete_ts = df[df["label"] == "Delete Purchase Order Item"].groupby(
    "(case) Case Identifier")["timestamp"].first()

time_wasted = (delete_ts - create_ts.reindex(delete_ts.index)).dropna()
print(f"\n  Time elapsed from Create PO to Delete PO:")
print(f"    Mean:   {time_wasted.mean()}")
print(f"    Median: {time_wasted.median()}")
print(f"    Min:    {time_wasted.min()}")
print(f"    Max:    {time_wasted.max()}")

# ── Cancel Invoice Receipt: rework cascade analysis ───────────────────────────

print("\n── Cancel Invoice Receipt: rework cascade ────────────────────")

cir_cases = df[df["label"] == "Cancel Invoice Receipt"]["(case) Case Identifier"].unique()
cir_df    = df[df["(case) Case Identifier"].isin(cir_cases)]

# Check overlap with Vendor creates debit memo
debit_cases = df[df["label"] == "Vendor creates debit memo"]["(case) Case Identifier"].unique()
overlap     = set(cir_cases) & set(debit_cases)
print(f"  Cases with Cancel Invoice Receipt:          {len(cir_cases):,}")
print(f"  Of those, also have Vendor debit memo:      {len(overlap):,} ({len(overlap)/len(cir_cases)*100:.1f}%)")

# Activities that follow Cancel Invoice Receipt
activities_after_cancel = []
for case_id, grp in cir_df.groupby("(case) Case Identifier"):
    acts = grp.sort_values("timestamp")["label"].tolist()
    # Find all occurrences (some cases cancel more than once)
    for i, act in enumerate(acts):
        if act == "Cancel Invoice Receipt" and i + 1 < len(acts):
            activities_after_cancel.append(acts[i + 1])

print("\n  Activities immediately following Cancel Invoice Receipt:")
for act, count in Counter(activities_after_cancel).most_common():
    print(f"    {count:5,}  {act}")

# ── Cancel Goods Receipt: cascade analysis ────────────────────────────────────

print("\n── Cancel Goods Receipt: cascade analysis ────────────────────")

cgr_cases = df[df["label"] == "Cancel Goods Receipt"]["(case) Case Identifier"].unique()
cgr_df    = df[df["(case) Case Identifier"].isin(cgr_cases)]

print(f"  Cases with Cancel Goods Receipt: {len(cgr_cases):,}")

activities_after_cgr = []
for case_id, grp in cgr_df.groupby("(case) Case Identifier"):
    acts = grp.sort_values("timestamp")["label"].tolist()
    for i, act in enumerate(acts):
        if act == "Cancel Goods Receipt" and i + 1 < len(acts):
            activities_after_cgr.append(acts[i + 1])

print("  Activities immediately following Cancel Goods Receipt:")
for act, count in Counter(activities_after_cgr).most_common():
    print(f"    {count:5,}  {act}")

# How many CGR cases also trigger Cancel Invoice Receipt?
cgr_then_cir = set(cgr_cases) & set(cir_cases)
print(f"\n  CGR cases that also have Cancel Invoice Receipt: {len(cgr_then_cir):,} "
      f"({len(cgr_then_cir)/len(cgr_cases)*100:.1f}%)")
