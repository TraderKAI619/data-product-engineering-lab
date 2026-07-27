# User Journey

## Purpose

This document describes how users interact with the product throughout their lifecycle.

The objective is to connect business activities with product events before defining event schemas and analytics pipelines.

Every event documented in **ProductEventTaxonomy.md** should originate from a meaningful user interaction.

---

# Product Scenario

This project simulates a subscription-based Software-as-a-Service (SaaS) platform.

Users visit the website, evaluate the product, and may eventually subscribe to a paid plan.

The Product Analytics platform tracks each important interaction to measure business performance and ensure data quality.

---

# Primary User Journey

```text
Visitor
    │
    ▼
Landing Page
    │
    ▼
Sign Up
    │
    ▼
Login
    │
    ▼
Explore Features
    │
    ▼
Upgrade Plan
    │
    ▼
Checkout
    │
    ▼
Payment
    │
    ▼
Subscription Activated
```

This journey represents the primary customer lifecycle supported in Version 1.0.

---

# Journey Breakdown

| Step | User Goal | Business Goal | Expected Event |
|------|-----------|---------------|----------------|
| Landing Page | Learn about the product | Acquire qualified visitors | landing_page_view |
| Sign Up | Create an account | Acquire registered users | sign_up |
| Login | Access the platform | Increase active users | login |
| Explore Features | Evaluate product value | Increase product engagement | feature_view |
| Upgrade Plan | Choose a paid subscription | Increase subscription intent | upgrade_plan |
| Checkout | Confirm subscription purchase | Complete conversion | checkout_started |
| Payment | Complete payment | Generate revenue | payment_success |
| Subscription Activated | Access premium features | Activate subscription | subscription_activated |

---

# Business Funnel

Version 1.0 focuses on the following subscription conversion funnel.

```text
Landing Page
      │
      ▼
Sign Up
      │
      ▼
Login
      │
      ▼
Feature View
      │
      ▼
Upgrade Plan
      │
      ▼
Checkout Started
      │
      ▼
Payment Success
      │
      ▼
Subscription Activated
```

The funnel represents the primary business flow used to calculate Product KPIs and validate data quality.

---

# KPI Mapping

| KPI | Required Events |
|------|-----------------|
| Visitor-to-Sign-up Rate | landing_page_view, sign_up |
| Login Rate | sign_up, login |
| Feature Adoption Rate | login, feature_view |
| Upgrade Rate | feature_view, upgrade_plan |
| Checkout Rate | upgrade_plan, checkout_started |
| Payment Success Rate | checkout_started, payment_success |
| Payment Failure Rate | checkout_started, payment_failed |
| Subscription Conversion Rate | sign_up, subscription_activated |

---

# Journey Design Principles

## 1. Business Before Technology

The journey represents business interactions rather than implementation details.

---

## 2. One Journey, One Source of Truth

Every business event should map to one meaningful customer action.

---

## 3. KPI-Driven Design

Each major journey step should contribute to at least one measurable business KPI.

Interactions that provide no analytical value should not be tracked in Version 1.0.

---

## 4. Data Quality Starts with User Behavior

Reliable analytics begin with a clearly defined customer journey.

A well-defined journey makes it easier to validate event completeness, identify missing events, and investigate anomalies.

---

## 5. Incremental Scope

Version 1.0 focuses on the primary subscription conversion funnel.

Additional journeys—such as subscription renewal, cancellation, password recovery, and marketing attribution—will be introduced in future iterations.

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