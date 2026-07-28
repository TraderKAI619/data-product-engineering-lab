# Business Anomaly Design

## Overview

This document defines the first business anomaly scenario used in the **Data Product Engineering Lab**.

Unlike data quality issues (missing values, duplicates, schema violations), a business anomaly represents a situation where the data remains structurally correct while the underlying business behavior changes unexpectedly.

The objective is to simulate a realistic production incident that can be detected through product analytics while still passing all schema validation rules.

---

# Business Problem

A Product Analytics dashboard shows that the overall conversion rate has suddenly dropped.

Initial investigation confirms that:

- ETL pipeline completed successfully.
- No schema violations were detected.
- No missing values or duplicate primary keys exist.
- Event ordering remains valid.
- All Data Contract rules are satisfied.

The engineering team's next question becomes:

> **Is this a data quality issue, or is the business actually experiencing an abnormal event?**

To answer this question, the synthetic dataset intentionally injects a realistic business anomaly while keeping the dataset structurally valid.

---

# Design Principle

This repository intentionally separates two fundamentally different classes of problems.

## Data Quality Issue

Examples:

- Missing values
- Duplicate primary keys
- Invalid schema
- Incorrect timestamps
- Broken event relationships

These problems indicate that the dataset itself cannot be trusted.

---

## Business Anomaly

Examples:

- Payment gateway outage
- Checkout conversion drop
- Marketing campaign traffic surge
- Product feature regression

These scenarios represent genuine business incidents.

The dataset remains correct.

The business behavior becomes abnormal.

This distinction is the core concept of this repository.

---

# Scenario

## Name

Payment Gateway Failure

---

## Description

During **Day 21** of the observation window, the payment gateway experiences a temporary service degradation.

Users are still able to:

- Browse the product
- Login
- View premium features
- Start checkout

However, a significant portion of payment requests fail before completing the purchase.

As a result:

- Payment Success decreases
- Payment Failure increases
- Overall subscription conversion decreases

The remainder of the customer journey remains unchanged.

---

# Scope

Version 1.0 intentionally implements only a single business anomaly.

Affected population:

- All users

Affected platform:

- All platforms

Affected country:

- All countries

Affected period:

- Day 21 only

Future versions may introduce:

- Regional incidents
- Platform-specific failures
- Hour-level outages
- User segment targeting

Those scenarios are intentionally deferred to future iterations.

---

# Time Window Definition

The generator stores timestamps as concrete datetimes.

Therefore, **Day 21** is defined relative to the configured observation window.

Example:

```
CONFIG.start_date = 2026-01-01
```

The anomaly window is:

```
2026-01-21 00:00:00
    ≤ checkout_started
< 2026-01-22 00:00:00
```

The checkout initiation time determines whether a checkout belongs to the incident window.

This definition avoids ambiguity around payments that complete shortly after midnight while remaining consistent with the repository's day-based simulation model.

---

# Target Metrics

Baseline payment success rate:

```
Approximately 91%
```

Target payment success rate during Day 21:

```
Approximately 42%
```

Outside the anomaly window:

```
Remain unchanged
```

The objective is to produce a measurable conversion decline without introducing invalid data.

---

# Injection Strategy

Business anomalies are injected **after** the clean dataset has been generated and validated.

Pipeline:

```
Generate Clean Dataset
        │
        ▼
Validate Schema
        │
        ▼
Inject Business Anomaly
        │
        ▼
Validate Schema Again
        │
        ▼
Export Final Dataset
```

The clean dataset is never regenerated.

Instead, the anomaly is injected by modifying existing business outcomes.

---

# Injection Algorithm

Version 1.0 uses an event modification strategy.

1. Identify every checkout whose **checkout_started** event falls inside the Day 21 window.

2. For each affected checkout:

   - Re-evaluate the payment outcome using the anomaly success rate (~42%).

3. If the checkout is converted from **payment_success** to **payment_failed**:

   - Change the payment event to `payment_failed`.
   - Remove the corresponding `subscription_activated` event.

4. If the checkout remains successful:

   - No further modification is required.

No additional events are inserted.

No schema is modified.

Only business outcomes are updated.

---

# Design Constraints

The anomaly injection must preserve the structural integrity of the dataset.

Specifically:

- No duplicate event IDs
- No invalid event names
- No broken checkout relationships
- No invalid timestamps
- No invalid event ordering
- No cardinality violations

The injected dataset must continue to satisfy every schema validation rule established in Commit 6.

---

# Validation Expectations

Schema Validation should continue to report:

```
Schema validation passed.
```

The anomaly should only affect business KPIs.

It must never introduce data quality problems.

---

# Expected Dashboard Behavior

Compared with the clean dataset:

- Payment Success decreases sharply.
- Payment Failure increases sharply.
- Overall conversion rate decreases.
- Checkout volume remains approximately unchanged.

The dashboard should indicate:

```
Traffic remains stable.

Checkout volume remains stable.

Payment Success suddenly drops.

Payment Failure suddenly spikes.
```

This strongly suggests a payment infrastructure issue rather than a traffic acquisition problem.

---

# Why This Scenario?

This repository is designed to answer one central question:

> **Can we trust the dashboard?**

Answering that question requires distinguishing between:

- Broken data
- Broken business

A payment gateway outage is one of the most common real-world production incidents where:

- Data pipelines continue operating normally.
- Data contracts remain valid.
- Business KPIs deteriorate rapidly.

Therefore, it serves as the ideal first business anomaly.

---

# Future Iterations

The following scenarios are intentionally deferred.

## Regional Incident

Example:

- JP payment outage
- TW and US remain normal

---

## Marketing Campaign

Example:

- Landing Page traffic spikes
- Signup remains stable
- Conversion rate decreases

---

## Feature Regression

Example:

- Feature View remains stable
- Upgrade conversion decreases

---

## Platform-specific Incident

Example:

- Mobile checkout failure
- Web remains unaffected

---

## Hour-level Incident

Example:

- Service outage from 13:00 to 16:00

---

# Out of Scope

Version 1.0 intentionally does not simulate:

- Data Quality Issues
- Schema Drift
- Late-arriving Events
- Duplicate Events
- Missing Values
- Corrupted Primary Keys

Those scenarios belong to the Data Quality module and are implemented separately.

---

# Version

Version:

```
Business Anomaly v1.0
```

Implemented scenario:

```
Payment Gateway Failure
```

Design philosophy:

> **Schema Valid, Business Abnormal**