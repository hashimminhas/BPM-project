# BPM-PROJ LTAT.05.025 Business Process Mining

CoatXR Procure-to-Pay process analysis for 10 vendors.  
**Team:** Hashim, Calvin, Ahmed, Shokat   
**University of Tartu · May 2026**

---



## Task Status & Ownership

| Task | Description | Owner | Status |
|------|-------------|-------|--------|
| Task 1 | Event log inspection — column analysis, distributions, relationships | Hashim Ali | ✅ Done |
| Task 2 | Process understanding — Apromore maps, bottleneck analysis, variant comparison | Hashim Ali | ✅ Done |
| Task 3 | SLA compliance — violation rate per spend area | Hashim Ali | ✅ Done |
| Task 4 | Deviations from ideal flow — deviation types and frequencies | Ahmed | ✅ Done |
| Task 5 | Process milestones — phase durations (P0–P3) | Shokat Zaman | ✅ Done |
| Task 6 | Seasonality — WiP over time, monthly and weekday patterns | Shokat Zaman | ✅ Done |
| Task 7 | Rework loops — top 3 loops and cycle time impact | Shokat Zaman | ✅ Done |
| Task 8 | Cancellations & deletions — over-processing analysis | Ahmed | ✅ Done |
| Task 9 | Effects of change activities — cycle time impact per change type | Ahmed | ✅ Done |
| Task 10 | Vendor comparison (Labels) — cycle time and directly-follows analysis | Calvin | ✅ Done |
| Task 11 | Free-form analysis — case vs document granularity comparison | Calvin | ✅ Done |

---

## About `coatxr_cases_shared.csv`

Extracted in Task 1 by Hashim. One row per case with pre-computed cycle time.  
Used in: **Tasks 3, 5, 6, 7, 8, 9, 10, 11** — import this instead of the raw `.gz`.

```python
import pandas as pd
df = pd.read_csv('data/coatxr_cases_shared.csv')
```

