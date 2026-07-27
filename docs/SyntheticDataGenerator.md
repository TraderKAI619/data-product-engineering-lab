# Synthetic Data Generator

## Purpose

This module generates realistic Product Analytics events based on the business journey defined in `UserJourney.md`.

The generated dataset serves as the source data for the complete analytics pipeline:

- Databricks Bronze Layer
- Silver Layer
- Gold Layer
- KPI SQL Models
- Product Analytics Dashboard
- Data Quality Validation
- Root Cause Investigation

The objective is not simply to generate fake data, but to simulate realistic customer behavior and controlled business/data quality incidents.

---

# Configuration

Version 1.0 targets Databricks Community Edition.

```python
CONFIG = {
    "num_users": 5000,
    "start_date": "2026-01-01",
    "days": 30,
    "random_seed": 42
}
```

The dataset size should remain small enough to execute the complete pipeline efficiently while still producing realistic business patterns.

Expected output:

- Users: ~5,000
- Events: ~40,000–80,000

---

# Generator Pipeline

```text
Generate Users
        │
        ▼
Generate Sessions
        │
        ▼
Simulate User Journey
        │
        ▼
Generate Events
        │
        ▼
Validate Event Schema
        │
        ▼
Export Clean Dataset
        │
        ▼
Inject Business Anomalies
        │
        ▼
Inject Data Quality Issues
        │
        ▼
Export Final Dataset
```

The clean dataset provides the baseline for validating the analytics pipeline before introducing controlled anomalies.

---

# Module Structure

```python
generate_users()

generate_sessions()

simulate_user_journey()

generate_events()

validate_schema()

export_clean_dataset()

inject_business_anomalies()

inject_data_quality_issues()

export_final_dataset()
```

Each module performs a single responsibility to simplify testing and debugging.

---

# Customer Journey Simulation

```text
landing_page_view
        │
        ├────────── Leave
        │
        ▼
sign_up
        │
        ├────────── Leave
        │
        ▼
login
        │
        ▼
feature_view
        │
        ├────────── Leave
        │
        ▼
upgrade_plan
        │
        ▼
checkout_started
        │
        ├────────── payment_failed
        │
        ▼
payment_success
        │
        ▼
subscription_activated
```

---

# Default Funnel Probability

| Journey | Probability |
|----------|------------:|
| Landing → Sign Up | 18% |
| Sign Up → Login | 93% |
| Login → Feature View | 88% |
| Feature View → Upgrade | 27% |
| Upgrade → Checkout | 82% |
| Checkout → Payment Success | 91% |
| Payment Success → Subscription Activated | 99% |

These probabilities produce a realistic subscription conversion funnel while remaining easy to understand during demonstrations.

---

# Business Anomaly Scenarios

## Scenario 1 — Payment Service Incident

**Period**

Day 21

**Injected Change**

Payment Success Rate:

91%

↓

42%

Expected observable impact:

- Payment Failure Rate ↑
- Subscription Conversion ↓
- Checkout volume remains stable

This simulates a business incident rather than a data quality issue.

---

## Scenario 2 — Marketing Campaign

**Period**

Day 10

Landing Page Visitors:

+180%

Expected observable impact:

- Traffic increases
- Funnel conversion remains stable

---

## Scenario 3 — Feature Release

**Period**

Day 15

Feature Adoption Rate:

+25%

Expected observable impact:

- Feature View increases
- Upgrade Rate improves

---

# Data Quality Scenarios

The following issues are intentionally injected after generating the clean dataset.

| Scenario | Injection Rule | Purpose |
|----------|----------------|---------|
| Missing Events | Remove 15% of `payment_success` events on Days 12–14 | Simulate ingestion failure |
| Duplicate Events | Duplicate 2% of `login` events across the dataset | Simulate duplicate ingestion |
| Late Events | Delay 5% of events by 1–3 days | Simulate delayed event arrival |

Schema Drift is intentionally excluded from Version 1.0 and will be implemented in a future iteration.

---

# Validation Rules

Every generated event must satisfy:

- EventSchema.md
- ProductEventTaxonomy.md
- UserJourney.md

Validation includes:

- Required fields
- Valid event names
- Schema version
- Checkout relationship integrity
- Timestamp consistency

Datasets that fail validation should not be exported.

---

# Output

```
data/

    clean_events.parquet

    events.parquet
```

The clean dataset is used to verify the analytics pipeline.

The final dataset includes controlled business anomalies and data quality issues.

---

# Development Roadmap

## Commit 1

```
feat: create synthetic data generator skeleton
```

---

## Commit 2

```
feat: generate clean synthetic dataset
```

---

## Commit 3

```
feat: simulate customer journey
```

---

## Commit 4

```
feat: generate business events
```

---

## Commit 5

```
feat: inject business anomaly scenarios
```

---

## Commit 6

```
feat: inject data quality issues
```

---

## Commit 7

```
feat: export parquet datasets
```

---

# Relationship to Other Documents

```text
BusinessProblem.md
        │
        ▼
UserJourney.md
        │
        ▼
ProductEventTaxonomy.md
        │
        ▼
EventSchema.md
        │
        ▼
SyntheticDataGenerator
        │
        ▼
clean_events.parquet
        │
        ▼
events.parquet
        │
        ▼
Databricks Bronze
        │
        ▼
Silver
        │
        ▼
Gold
        │
        ▼
Product Analytics Dashboard
        │
        ▼
Data Quality Validation
        │
        ▼
Root Cause Investigation
``` 