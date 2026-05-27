"""
LTAT.05.025 – Business Process Mining: CoatXR Project
Task 4: Deviations from Ideal Flow

Identifies how many cases follow the ideal BPMN model perfectly,
and classifies the most common deviations.

Authors: [Team names]
"""

import pandas as pd
from collections import Counter

# ── Configuration ─────────────────────────────────────────────────────────────

DATA_PATH = "P2P_CoatXR_10_vendors.csv"

# The five milestone activities of the ideal process model
IDEAL_MILESTONES = [
    "Create Purchase Order Item",
    "Record Goods Receipt",
    "Vendor creates invoice",
    "Record Invoice Receipt",
    "Clear Invoice",
]

# ── Load and prepare data ─────────────────────────────────────────────────────

df = pd.read_csv(DATA_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values(["(case) Case Identifier", "timestamp"])

# Per-case attributes
case_activities = df.groupby("(case) Case Identifier")["label"].apply(list)
item_category   = df.groupby("(case) Case Identifier")["(case) Item Category"].first()
case_last_event = df.groupby("(case) Case Identifier")["label"].last()

# A case is completed if its last event is Clear Invoice or Record Goods Receipt
completed_cases = case_last_event[
    case_last_event.isin(["Clear Invoice", "Record Goods Receipt"])
].index

# Exclude Consignment cases (they follow a different, unmodeled process)
non_consignment = [
    c for c in case_activities.index
    if "Consignment" not in str(item_category.get(c, ""))
]
nc_completed = [c for c in non_consignment if c in completed_cases]

print(f"Total cases:                        {len(case_activities)}")
print(f"Consignment cases (excluded):       {len(case_activities) - len(non_consignment)}")
print(f"Non-consignment cases (scope):      {len(non_consignment)}")
print(f"  of which completed:               {len(nc_completed)}")

# ── Ideal flow check ──────────────────────────────────────────────────────────

def is_ideal_flow(activities: list) -> bool:
    """
    Returns True if the case follows the ideal BPMN model exactly:
      1. Only milestone activities are present (no extras)
      2. First activity is Create Purchase Order Item
      3. Middle two are Record Goods Receipt and Vendor creates invoice (any order)
      4. Fourth activity is Record Invoice Receipt
      5. Last activity is Clear Invoice
    """
    milestones     = [a for a in activities if a in IDEAL_MILESTONES]
    non_milestones = [a for a in activities if a not in IDEAL_MILESTONES]

    if non_milestones:
        return False  # Extra activities present
    if len(milestones) != 5:
        return False  # Wrong number of milestone occurrences
    if milestones[0] != "Create Purchase Order Item":
        return False
    if milestones[-1] != "Clear Invoice":
        return False
    if milestones[-2] != "Record Invoice Receipt":
        return False
    if sorted(milestones[1:3]) != sorted(["Record Goods Receipt", "Vendor creates invoice"]):
        return False
    return True


ideal_all       = sum(1 for c in non_consignment if is_ideal_flow(case_activities[c]))
ideal_completed = sum(1 for c in nc_completed    if is_ideal_flow(case_activities[c]))

print(f"\n── Ideal flow conformance ───────────────────────────────")
print(f"Cases following ideal flow (all scope):       {ideal_all} ({ideal_all/len(non_consignment)*100:.1f}%)")
print(f"Cases following ideal flow (completed only):  {ideal_completed} ({ideal_completed/len(nc_completed)*100:.1f}%)")

# ── Deviation classification ──────────────────────────────────────────────────

def get_deviations(activities: list) -> list:
    """
    Returns a list of deviation labels for a given case.
    Each deviation is either:
      - 'Extra activity: <name>'  — a non-milestone activity is present
      - 'Missing: <milestone>'    — an expected milestone is absent
    """
    deviations = []

    # Extra (non-modeled) activities
    extra = [a for a in activities if a not in IDEAL_MILESTONES]
    for act in set(extra):
        deviations.append(f"Extra activity: {act}")

    # Missing milestones
    for milestone in IDEAL_MILESTONES:
        if milestone not in activities:
            deviations.append(f"Missing: {milestone}")

    return deviations


# Count how many cases exhibit each deviation type
all_deviations = []
for c in non_consignment:
    all_deviations.extend(get_deviations(case_activities[c]))

deviation_counts = Counter(all_deviations)

print(f"\n── Deviation frequency (% of {len(non_consignment)} non-consignment cases) ──")
for deviation, count in deviation_counts.most_common(15):
    pct = count / len(non_consignment) * 100
    print(f"  {pct:5.1f}%  ({count:6,})  {deviation}")

# ── Variant analysis (completed cases) ───────────────────────────────────────

print(f"\n── Top 10 process variants (completed non-consignment cases) ──")
variant_counter = Counter(
    tuple(case_activities[c]) for c in nc_completed
)
for variant, count in variant_counter.most_common(10):
    pct = count / len(nc_completed) * 100
    print(f"  {pct:5.1f}%  ({count:5,})  {list(variant)}")
