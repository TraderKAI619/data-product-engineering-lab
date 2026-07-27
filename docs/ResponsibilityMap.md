# Responsibility Map

## Purpose

This document explains how the scope of this project was determined.

Rather than implementing every possible technology, the project prioritizes the areas that provide the strongest evidence of Product Engineering capability by combining:

- Official Job Description
- Hiring Manager feedback
- Personal technical assessment
- Available implementation resources

The objective is **not** to replicate a production system.

Instead, this project demonstrates the decision-making process behind designing a modern Data Product.

---

## Responsibility Mapping

| Responsibility | Official JD | Hiring Manager Feedback | Project Response |
|----------------|-------------|--------------------------|------------------|
| Product Thinking | Own Data Collection products | Expected ownership across the product lifecycle | Business Problem + Product Documentation |
| SQL | Required | Primary development language | SQL-first Analytics Pipeline |
| Databricks | Not mentioned in the JD | Confirmed by the Hiring Manager as a core technology | Databricks Community Edition |
| Dashboard | KPI monitoring and product metrics | Dashboard visibility is important | Product Analytics Dashboard |
| Event Tracking | Required | Core responsibility | Event Tracking Design |
| Event Schema | Required | Important for data consistency | Event Schema Documentation |
| SDK Instrumentation | Mentioned | Useful but not the highest priority | Minimal Web Event Tracking |
| Data Quality | KPI reliability | One of the highest priorities | Data Quality Validation Framework |
| AI Tooling | AI-assisted development | Important for future workflow | AI-assisted Investigation Workflow *(Future Iteration)* |
| Stakeholder Communication | Cross-functional collaboration | Strong communication expected | Product Documentation + Decision Log |

---

## Design Principles

### 1. Everything must be runnable.

Every major component should be implemented and executable.

Documentation should describe working solutions rather than hypothetical ideas.

---

### 2. Everything must be explainable.

Every technical decision should have a clear business reason.

Implementation choices must always support a business objective instead of demonstrating technology for its own sake.

---

### 3. Prioritize depth over breadth.

Rather than implementing every available technology, the project focuses on demonstrating a strong understanding of the responsibilities that matter most.

Depth of implementation is preferred over feature quantity.

---

### 4. Prioritize based on real-world signals, not assumptions.

Implementation priorities are determined by combining publicly available information with direct feedback from the Hiring Manager.

Instead of relying solely on the written Job Description, this project prioritizes technologies and capabilities that were consistently identified as the highest-value areas, including:

- SQL
- Databricks
- Product Analytics
- Dashboard Design
- Data Quality

Lower-priority topics, such as building a complete production SDK, are intentionally deferred.

---

## What This Project Does NOT Try To Demonstrate

This project intentionally does **not** attempt to demonstrate:

- Production-scale distributed systems
- Kafka or streaming architectures
- Mobile SDK development
- Enterprise infrastructure
- Multi-region cloud deployment

These topics are valuable in real production environments, but they fall outside the scope of Version 1.0.

The focus of this project is to demonstrate Product Engineering thinking through realistic business scenarios, trustworthy analytics, and well-structured technical decisions.

---

## Project Philosophy

This project follows one simple principle:

> **Technology exists to support trustworthy business decisions.**

Every document, dataset, SQL model, dashboard, and data quality rule should ultimately answer one question:

> **Can stakeholders trust the Product Analytics Dashboard?**

If a feature does not contribute toward answering that question, it should not be included in Version 1.0.