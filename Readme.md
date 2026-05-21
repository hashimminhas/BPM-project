# BPM-PROJ — LTAT.05.025 Business Process Mining

CoatXR Procure-to-Pay process analysis for 10 vendors.  
**Team:** Hashim Ali, Calvin, Ahmed, Shokat

---

## Project Structure

```
data/
├── P2P_CoatXR_10_vendors_csv.gz   # Raw event log (311,821 events, 59,385 cases)
└── coatxr_cases_shared.csv        # Cleaned case-level data extracted in Task 1
```

## Task Status

| Task | Description | Status | Owner |
|------|-------------|--------|-------|
| Task 1 | Event log inspection | ✅ Done | Hashim |
| Task 2 | Process understanding (Apromore) | 🔄 In Progress | Hashim |
| Task 3–11 | Remaining analysis | ⏳ Pending | All |

## About `coatxr_cases_shared.csv`

Extracted in Task 1. One row per case with pre-computed cycle time.  
Used in: **Tasks 3, 5, 6, 7, 8, 9, 10, 11** — import this instead of the raw `.gz`.

```python
import pandas as pd
df = pd.read_csv('data/coatxr_cases_shared.csv')
```

## Submission Deadline: 28 May 2026