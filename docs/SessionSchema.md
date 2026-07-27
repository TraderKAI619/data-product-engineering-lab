# Session Schema

## Purpose

The Session dataset represents individual user visits to the product.

Each session belongs to one user.

A single user can have multiple sessions over time.

The Session dataset bridges the User Master and Event datasets.

---

## Session Schema

| Column | Type | Description |
|---------|------|-------------|
| session_id | STRING | Unique session identifier |
| user_id | STRING | Foreign key to User Master |
| session_start | TIMESTAMP | Session start timestamp |
| platform | STRING | User platform (Web / Mobile) |

---

## Relationships

```text
User Master (1)
      │
      ▼
 Session (N)
      │
      ▼
 Events (N)
```

---

## Validation Rules

- `session_id` must be unique.
- `user_id` must exist in the User Master.
- `session_start` must be greater than or equal to `signup_date`.
- `platform` must be either `Web` or `Mobile`.
- No null values are allowed.

---

## Relationship to Other Documents

```text
UserJourney.md
        │
        ▼
SessionSchema.md
        │
        ▼
EventSchema.md
        │
        ▼
synthetic_data_generator.py
```

This document defines the Session data model used by the synthetic data generator.

The implementation will follow this specification during dataset generation.