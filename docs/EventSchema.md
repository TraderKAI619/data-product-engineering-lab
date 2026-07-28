# Event Schema

## Purpose

This document defines the structure of every business event used in Version 1.0.

The objective is to establish a consistent event model before generating synthetic data or building analytics pipelines.

All downstream components—including Databricks, SQL models, dashboards, and data quality validation—depend on the schemas defined in this document.

---

# Common Event Schema

Every business event shares the following common attributes.

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| event_id | UUID | Yes | Unique identifier for the event |
| event_name | STRING | Yes | Business event name |
| event_version | STRING | Yes | Business event version (e.g., v1) |
| schema_version | STRING | Yes | Schema version identifier |
| user_id | STRING | Yes | User identifier |
| session_id | STRING | Yes | User session identifier |
| event_timestamp | TIMESTAMP | Yes | Event occurrence timestamp (business time) |
| ingestion_timestamp | TIMESTAMP | Yes | Time the event was received by the data platform (platform time) |
| platform | STRING | Yes | Web / Mobile |
| device_type | STRING | Yes | Desktop / Mobile / Tablet |
| country | STRING | Yes | User country |
| app_version | STRING | No | Application version |
| traffic_source | STRING | No | Marketing acquisition source |

---

## event_timestamp vs. ingestion_timestamp

These two fields represent different points in time and are intentionally kept separate.

- **event_timestamp** — When the business event actually occurred (business chronology).
- **ingestion_timestamp** — When the event was received by the data platform (platform chronology).

In the clean dataset, the two are always equal: every event is assumed to be ingested immediately as it occurs.

A **Late-arriving Events** Data Quality issue (see `DataQualityInjection.md`) simulates delayed ingestion by shifting `ingestion_timestamp` forward while leaving `event_timestamp` unchanged. This preserves:

- Business chronology (the order in which things actually happened)
- Schema Validation Rule 5a / 5b (which are evaluated using `event_timestamp`)

while still allowing Freshness-related metrics (which are evaluated using `ingestion_timestamp`) to detect the delay.

---

# Event Schemas

## landing_page_view

### Purpose

Represents a visitor arriving at the landing page.

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| landing_page | STRING | Yes | Landing page URL |
| campaign_id | STRING | No | Marketing campaign identifier |

---

## sign_up

### Purpose

Represents successful account registration.

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| signup_method | STRING | Yes | Email / Google / Apple |
| referral_code | STRING | No | Referral code |

---

## login

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| login_method | STRING | Yes | Email / SSO |

---

## feature_view

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| feature_name | STRING | Yes | Feature viewed |

---

## upgrade_plan

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| current_plan | STRING | Yes | Current subscription plan |
| target_plan | STRING | Yes | Selected subscription plan |

---

## checkout_started

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| checkout_id | STRING | Yes | Unique checkout identifier |
| plan_name | STRING | Yes | Selected subscription plan |
| price | DECIMAL | Yes | Expected payment amount |
| currency | STRING | Yes | Currency |

---

## payment_success

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| checkout_id | STRING | Yes | Checkout identifier |
| payment_method | STRING | Yes | Payment method |
| amount | DECIMAL | Yes | Paid amount |
| currency | STRING | Yes | Currency |

---

## payment_failed

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| checkout_id | STRING | Yes | Checkout identifier |
| payment_method | STRING | Yes | Payment method |
| failure_reason | STRING | Yes | Failure reason |

---

## subscription_activated

### Purpose

Represents the successful activation of a paid subscription.

The subscription activation time is represented by the common `event_timestamp` field. No additional activation timestamp is required in Version 1.0.

### Additional Fields

| Field | Type | Required | Description |
|--------|------|----------|-------------|
| checkout_id | STRING | Yes | Checkout identifier |
| subscription_plan | STRING | Yes | Activated subscription plan |

---

# Schema Design Principles

## 1. Consistency

Every business event follows the same common schema.

---

## 2. Extensibility

Business-specific attributes are defined independently for each event.

---

## 3. Validation

Required fields must be validated before entering the analytics pipeline.

---

## 4. Backward Compatibility

Schema evolution should avoid breaking downstream analytics.

---

## 5. Traceability

Business events that belong to the same customer transaction should be linked through a shared business identifier (for example, `checkout_id`) rather than inferred using timestamps alone.

---

## 6. Event Time vs. Ingestion Time

Business occurrence time (`event_timestamp`) and platform ingestion time (`ingestion_timestamp`) are modeled as distinct fields. This separation allows the repository to simulate realistic data platform delays (Late-arriving Events) without corrupting business chronology or violating event ordering rules.

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
Databricks Pipeline
        │
        ▼
SQL KPI Models
        │
        ▼
Product Analytics Dashboard
        │
        ▼
Data Quality Validation
```