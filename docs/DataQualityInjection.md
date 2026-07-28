# DataQualityInjection.md

**Version:** 1.0

**Status:** Final

**Related Documents**

- BusinessProblem.md
- BusinessAnomalyDesign.md
- SchemaValidation.md
- EventSchema.md
- UserJourney.md

---

# Overview

This document defines how Data Quality Issues are injected into the synthetic Product Analytics dataset.

Unlike Business Anomalies, which represent genuine business events, Data Quality Issues simulate imperfections introduced by the data platform itself.

The objective is to demonstrate that identical business symptoms may originate from completely different causes, and a reliable Data Product must distinguish between them.

---

# Business Problem

Modern analytics platforms frequently encounter abnormal dashboard metrics.

Examples include:

- Daily Active Users suddenly decrease
- Checkout volume unexpectedly drops
- Payment conversion declines

However, dashboard symptoms alone do not reveal the true cause.

The anomaly may originate from:

- a genuine business incident
- a data quality issue

This repository intentionally models both scenarios independently.

---

# Design Philosophy

Business behavior and data reliability are independent concerns.

## Business Anomaly

Business Anomalies represent real operational or customer behavior changes.

Examples:

- Payment Gateway Failure
- Marketing Campaign Surge
- Feature Regression

Characteristics

- Business behavior changes
- Schema remains valid
- Data remains trustworthy

---

## Data Quality Issue

Data Quality Issues originate from the data platform rather than the business itself.

Examples:

- Missing Events
- Duplicate Events
- Late-arriving Events

Characteristics

- Business behavior remains unchanged
- Data reliability deteriorates
- Dashboard results become misleading

---

## Core Principle

A trustworthy Data Product should answer two independent questions.

> Is the business behaving differently?

and

> Can the underlying data still be trusted?

These concerns are intentionally separated throughout this repository.

---

# Scope

Version 1.0 supports:

| Scenario | Supported |
|----------|-----------|
| Missing Events | ✅ |
| Duplicate Events | ✅ |
| Late-arriving Events | ✅ |

Excluded:

| Scenario | Status |
|----------|--------|
| Schema Drift | Future |
| Invalid Data Types | Future |
| Corrupted Payload | Future |
| Broken Foreign Keys | Future |
| Invalid Enum Values | Future |
| Cross-table Inconsistency | Future |

---

# Design Principles

## Preserve Structural Validity

Version 1.0 intentionally preserves dataset structural integrity after Data Quality Injection.

The objective is to simulate realistic Data Quality degradation while allowing the complete pipeline to execute successfully.

---

## Why Not Simulate Broken Checkout Chains?

A realistic missing event could remove a required checkout lifecycle event while leaving downstream events behind.

For example:

checkout_started

↓

(payment_success missing)

↓

subscription_activated

This correctly violates Rule 5b defined in SchemaValidation.md.

Such scenarios are intentionally excluded from Version 1.0 automatic generation because they would terminate the generation pipeline during Schema Validation.

Commit 6 already demonstrates that Rule 5b correctly detects these inconsistencies.

Version 1.0 instead focuses on executable end-to-end datasets while still exposing realistic Data Quality degradation.

---

# Relationship with Schema Validation

| Scenario | Schema Validation | Data Quality Monitoring |
|----------|------------------|-------------------------|
| Missing Events (safe scope) | ✅ Pass | Detect |
| Duplicate Events | ✅ Pass | Detect |
| Late-arriving Events | ✅ Pass | Detect |
| Broken Checkout Chain | ❌ Fail | Out of Scope (v1.0) |

Schema Validation verifies structural correctness.

Data Quality Monitoring evaluates operational data quality dimensions such as completeness, uniqueness, and freshness.

These two responsibilities intentionally remain separate.

---

# Injection Strategy

The processing pipeline is:

Generate Clean Dataset

↓

Schema Validation

↓

Business Anomaly Injection

↓

Data Quality Injection

↓

Schema Validation

↓

Export Final Dataset

Data Quality Injection never changes the event schema.

It only adjusts event records according to the configured Data Quality scenario.

---

# Supported Scenarios

## Missing Events

Purpose

Simulate event loss during data collection or ingestion.

Version 1.0 intentionally limits missing events to non-checkout events.

Candidate events

- landing_page_view
- feature_view

Characteristics

- Random subset removed
- checkout_id relationships remain intact
- Schema Validation passes

Expected signals

- Daily Event Count decreases
- Completeness decreases

---

## Duplicate Events

Purpose

Simulate duplicated event ingestion.

Candidate events

- login
- feature_view

Characteristics

- Duplicate records are generated
- Each duplicate receives a unique event_id
- Duplicate timestamps may be slightly offset to simulate repeated ingestion
- Session ordering remains valid

Expected signals

- Daily Event Count increases
- Duplicate Rate increases

---

## Late-arriving Events

Purpose

Simulate delayed arrival of otherwise valid events.

Late-arriving events represent delays introduced by the data platform rather than changes in business behavior.

Implementation details are intentionally defined by the underlying Event Schema and ingestion model (see EventSchema.md).

Data Quality Injection only simulates delayed arrival while preserving business event chronology and schema integrity.

Expected signals

- Freshness decreases
- Recent reports become temporarily incomplete
- Delayed Arrival metrics increase

---

# Dashboard Expectations

Business dashboards and Data Quality dashboards intentionally observe different signals.

| Metric | Expected Change |
|---------|----------------|
| Daily Event Count | ↓ |
| Duplicate Rate | ↑ |
| Missing Event Rate | ↑ |
| Freshness | ↓ |
| Payment Success Rate | Approximately Stable |

This separation enables downstream systems to distinguish Business Incidents from Data Quality degradation.

---

# Future Scope

Future versions may introduce:

- Broken checkout chains
- Foreign key violations
- Schema evolution
- Invalid enum values
- Type mismatches
- Corrupted payloads
- Cross-table inconsistencies

These scenarios intentionally remain outside Version 1.0 in order to preserve a fully executable end-to-end pipeline.

---

# Design Summary

Business Incident

Business Behaviour

↓

Business KPI Changes

↓

Schema Remains Valid

---

Data Quality Issue

Data Collection

↓

Completeness

Uniqueness

Freshness

↓

Schema Usually Remains Valid

---

A reliable Data Product should distinguish these two categories rather than treating every KPI anomaly as a business problem.

---

# Version

**Version:** 1.0

**Status:** Final

**Design Goal**

> Business Incidents change business behavior. Data Quality Issues change data reliability. A trustworthy Data Product must distinguish between them.