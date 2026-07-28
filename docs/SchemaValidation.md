# Schema Validation

## Purpose

The Synthetic Data Generator produces two datasets during each execution:

- `clean_events.parquet`
- `events.parquet`

Before either dataset is exported, its structural integrity must be validated.

The objective of schema validation is **not** to verify business performance (for example, conversion rates or payment success rate), but to ensure that the generated dataset satisfies the expected **data contract** and can be safely consumed by downstream analytics pipelines, dashboards, and data quality checks.

Business anomalies intentionally injected later (for example, payment service outages or abnormal payment failure spikes) are expected to modify **data distribution**, but must never break the dataset schema.

---

# Validation Rules

The following rules define the minimum structural requirements for the Events dataset.

---

# Rule 1 — Required Columns

Every generated event must contain the following common columns.

| Column | Nullable | Description |
|----------|-----------|-------------|
| event_id | No | Unique identifier of each event |
| session_id | No | Session identifier |
| user_id | No | User identifier |
| event_name | No | Product Analytics event type |
| event_timestamp | No | Event occurrence timestamp |
| platform | No | User platform |
| country | No | User country |
| checkout_id | Yes | Checkout lifecycle identifier |

Validation:

- Every required column exists.
- No required column is missing.

---

# Rule 2 — Data Types

Each column must conform to the expected data type.

| Column | Expected Type |
|----------|----------------|
| event_id | string |
| session_id | string |
| user_id | string |
| event_name | string |
| event_timestamp | datetime64[ns] |
| platform | string |
| country | string |
| checkout_id | string or null |

Validation:

- All columns match the expected data types.
- Datetime columns remain datetime after export/import.

---

# Rule 3 — Allowed Event Names

Only predefined Product Analytics events are allowed.

Allowed values:

- landing_page_view
- sign_up
- login
- feature_view
- upgrade_plan
- checkout_started
- payment_success
- payment_failed
- subscription_activated

Validation:

- Every event_name belongs to the predefined event taxonomy.
- Unknown event names are rejected.

---

# Rule 4 — checkout_id Relationship

checkout_id represents a checkout lifecycle.

Only checkout-related events are allowed to contain checkout_id.

## checkout_id Required

- checkout_started
- payment_success
- payment_failed
- subscription_activated

## checkout_id Forbidden

- landing_page_view
- sign_up
- login
- feature_view
- upgrade_plan

Validation:

- Required events must contain checkout_id.
- Forbidden events must have null checkout_id.
- checkout_id must never be an empty string.

---

# Rule 5 — Timestamp Ordering

Generated timestamps must preserve logical event ordering.

Validation is performed at two independent levels.

## Session-Level Ordering

Within the same session:

landing_page_view

↓

login

↓

feature_view

↓

upgrade_plan

↓

checkout_started

↓

payment_success / payment_failed

↓

subscription_activated

Validation:

- Event timestamps within the same session must be monotonically increasing.

---

## Checkout-Level Ordering

Within the same checkout_id:

checkout_started

↓

payment_success / payment_failed

↓

subscription_activated

Validation:

- checkout_started must occur before every downstream checkout event.
- payment_success and payment_failed cannot occur before checkout_started.
- subscription_activated cannot occur before payment_success.

This rule becomes especially important after business anomaly injection and data quality issue injection, where event timestamps may intentionally become less reliable.

---

# Rule 6 — Primary Key Integrity

Every generated event must have a unique event_id.

Validation:

- event_id contains no duplicate values.
- event_id contains no null values.

---

# Validation Scope

Version 1.0 validates only the **common event schema**.

Validated:

- Required columns
- Data types
- Allowed event names
- checkout_id relationships
- Timestamp ordering
- Primary key uniqueness

Not validated in Version 1.0:

- Event-specific additional fields defined in EventSchema.md
- Funnel conversion rates
- Country distribution
- Platform distribution
- Payment success rate
- Business anomalies
- Data quality issues

## Additional Fields

EventSchema.md defines additional attributes for specific event types.

Examples include:

- landing_page
- signup_method
- referral_code
- feature_name
- current_plan
- target_plan
- price
- currency
- failure_reason
- subscription_plan

These fields are **not yet generated** by `simulate_user_journey()` and are therefore **not enforced** by schema validation in Version 1.0.

Validation of event-specific fields will be introduced in a future iteration after those attributes become part of the generated dataset.

---

# Validation Workflow

Schema validation is executed twice during data generation.

```text
simulate_user_journey()

↓

validate_schema()

↓

export_clean_dataset()

↓

inject_business_anomalies()

↓

inject_data_quality_issues()

↓

validate_schema()

↓

export_final_dataset()
```

The first validation guarantees that the clean dataset satisfies the expected data contract.

The second validation guarantees that injected business anomalies modify only business behavior while preserving dataset structure.

---

# Design Principles

## 1. Fail Fast

Invalid datasets should immediately raise an exception.

Silent failures are not allowed.

---

## 2. Business Logic Separation

Schema validation verifies only structural correctness.

Business metrics and business behavior are validated independently.

---

## 3. Incremental Evolution

Validation rules evolve together with the dataset.

As new event attributes are introduced, corresponding validation rules should be added without breaking existing validation logic.

Future validation targets may include:

- schema_version
- experiment_id
- user_state
- subscription_state
- event-specific attributes
- event sequence validation

---

## 4. Deterministic

Validation must always produce identical results for the same dataset.

No randomness is allowed during validation.

---

## Design Philosophy

Schema validation protects the **Data Contract**, not the **Business Outcome**.

Even when business anomalies intentionally alter conversion rates, payment success rates, or user behavior, downstream consumers should still be able to trust that:

- the dataset structure is valid,
- every event conforms to the agreed schema,
- and any observed anomaly originates from business behavior rather than pipeline corruption.

This separation ensures that downstream dashboards answer the intended question:

> **Can we trust the dashboard?**

If the schema remains valid, then unusual metrics should be interpreted as genuine business signals rather than failures of the data pipeline.