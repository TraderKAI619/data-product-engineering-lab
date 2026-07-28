"""
Synthetic Data Generator

Generate realistic Product Analytics events for the Data Product Engineering Lab.

This module creates:

- Customer journey events
- Business anomaly scenarios
- Data quality scenarios

Outputs:
    - clean_events.parquet
    - events.parquet
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Configuration
# ============================================================

@dataclass
class GeneratorConfig:
    """Configuration for synthetic data generation."""

    num_users: int = 5000
    start_date: str = "2026-01-01"
    days: int = 30
    random_seed: int = 42

    output_dir: Path = Path("data")


CONFIG = GeneratorConfig()


# ============================================================
# Funnel Configuration
# ============================================================
# Baseline (business-as-usual) conversion funnel, as defined in
# UserJourney.md / SyntheticDataGenerator design doc.
#
# NOTE: `return_session_login` is a new parameter introduced in
# Commit 5 to independently gate login for non-first sessions.
# It is NOT the same as `signup_to_login`, which only governs the
# immediate post-signup login on the first session. This value
# (0.75) is a provisional assumption and should be revisited if
# real-world benchmarks suggest otherwise.

DEFAULT_FUNNEL_PROBABILITY = {
    "landing_to_signup": 0.18,
    "signup_to_login": 0.93,
    "return_session_login": 0.75,
    "login_to_feature": 0.88,
    "feature_to_upgrade": 0.27,
    "upgrade_to_checkout": 0.82,
    "checkout_to_payment_success": 0.91,
    "payment_success_to_subscription": 0.99,
}

VALID_EVENT_NAMES = {
    "landing_page_view",
    "sign_up",
    "login",
    "feature_view",
    "upgrade_plan",
    "checkout_started",
    "payment_success",
    "payment_failed",
    "subscription_activated",
}


# ============================================================
# Business Anomaly Configuration (Commit 7)
# ============================================================
# Defines the "Payment Gateway Failure" scenario, as documented in
# docs/BusinessAnomalyDesign.md. Kept centralized here (mirroring
# the DEFAULT_FUNNEL_PROBABILITY pattern) rather than as scattered
# class constants, so future anomaly scenarios can follow the same
# convention.

BUSINESS_ANOMALY = {
    "day": 21,  # 1-indexed day of the observation window
    "target_payment_success_rate": 0.42,
}


# ============================================================
# Data Quality Configuration (Commit 8)
# ============================================================
# Defines the three Data Quality scenarios documented in
# docs/DataQualityInjection.md. Candidate event lists are kept
# here (not hardcoded inside inject_data_quality_issues()) so the
# scenario definitions stay centrally managed, mirroring the
# BUSINESS_ANOMALY pattern.

DATA_QUALITY = {
    "missing_rate": 0.02,
    "missing_candidates": [
        "landing_page_view",
        "feature_view",
    ],
    "duplicate_rate": 0.01,
    "duplicate_candidates": [
        "login",
        "feature_view",
    ],
    "late_arrival_rate": 0.03,
    "late_arrival_hours": (12, 48),
    "late_arrival_candidates": [
        "login",
        "feature_view",
    ],
}


# ============================================================
# Generator
# ============================================================

class SyntheticDataGenerator:
    """Generate synthetic Product Analytics events."""

    # --------------------------------------------------------
    # Schema Validation Constants (Commit 6, extended in 7.5)
    # --------------------------------------------------------

    REQUIRED_COLUMNS = [
        "event_id",
        "session_id",
        "user_id",
        "event_name",
        "event_timestamp",
        "ingestion_timestamp",
        "platform",
        "country",
        "checkout_id",
    ]

    NON_NULLABLE_COLUMNS = [
        "event_id",
        "session_id",
        "user_id",
        "event_name",
        "event_timestamp",
        "ingestion_timestamp",
        "platform",
        "country",
    ]

    CHECKOUT_ID_REQUIRED_EVENTS = {
        "checkout_started",
        "payment_success",
        "payment_failed",
        "subscription_activated",
    }

    CHECKOUT_ID_FORBIDDEN_EVENTS = {
        "landing_page_view",
        "sign_up",
        "login",
        "feature_view",
        "upgrade_plan",
    }

    # NOTE: must include every event_name in VALID_EVENT_NAMES
    # (except payment_failed, which shares payment_success's rank
    # below). See _validate_timestamp_order() for the explicit
    # check that catches any event missing from this list.
    SESSION_LEVEL_ORDER = [
        "landing_page_view",
        "sign_up",
        "login",
        "feature_view",
        "upgrade_plan",
        "checkout_started",
        "payment_success",  # payment_failed shares this rank
        "subscription_activated",
    ]

    def __init__(self, config: GeneratorConfig):

        self.config = config

        # Ensure reproducibility
        random.seed(config.random_seed)
        np.random.seed(config.random_seed)

    # --------------------------------------------------------

    def run(self):

        logger.info("Starting synthetic data generation...")

        users = self.generate_users()
        logger.info("Users generated.")

        sessions = self.generate_sessions(users)
        logger.info("Sessions generated.")

        events = self.simulate_user_journey(users, sessions)
        logger.info("Customer journey simulated.")

        self.validate_schema(events)
        logger.info("Clean dataset validation passed.")

        self.export_clean_dataset(events)
        logger.info("Clean dataset exported.")

        events = self.inject_business_anomalies(events)
        logger.info("Business anomalies injected.")

        events = self.inject_data_quality_issues(events)
        logger.info("Data quality issues injected.")

        self.validate_schema(events)
        logger.info("Final dataset validation passed.")

        self.export_final_dataset(events)
        logger.info("Final dataset exported.")

        logger.info("Synthetic data generation completed.")

    # --------------------------------------------------------

    def generate_users(self) -> pd.DataFrame:
        """
        Generate the User Master dataset.

        Version 1.0 generates the minimal user profile required
        for downstream session and event generation.
        """

        logger.info("Generating user master...")

        countries = ["JP", "TW", "US"]
        country_weights = [0.80, 0.15, 0.05]

        platforms = ["Web", "Mobile"]
        platform_weights = [0.65, 0.35]

        start_date = pd.to_datetime(self.config.start_date)

        users = pd.DataFrame(
            {
                "user_id": [
                    f"U{i:06d}"
                    for i in range(1, self.config.num_users + 1)
                ],
                "country": np.random.choice(
                    countries,
                    size=self.config.num_users,
                    p=country_weights,
                ),
                "platform": np.random.choice(
                    platforms,
                    size=self.config.num_users,
                    p=platform_weights,
                ),
                "signup_date": (
                    start_date
                    + pd.to_timedelta(
                        np.random.randint(
                            low=0,
                            high=self.config.days,
                            size=self.config.num_users,
                        ),
                        unit="D",
                    )
                ),
            }
        )

        # =====================================================
        # Basic Validation
        # =====================================================

        assert len(users) == self.config.num_users, (
            "Unexpected number of users generated."
        )

        assert users["user_id"].is_unique, (
            "Duplicate user_id detected."
        )

        assert users.isnull().sum().sum() == 0, (
            "Null values detected."
        )

        assert set(users["country"].unique()).issubset(
            set(countries)
        ), "Invalid country detected."

        assert set(users["platform"].unique()).issubset(
            set(platforms)
        ), "Invalid platform detected."

        # =====================================================
        # Logging
        # =====================================================

        logger.info(
            "Generated %d users.",
            len(users),
        )

        logger.info(
            "Country distribution:\n%s",
            users["country"].value_counts().to_string(),
        )

        logger.info(
            "Platform distribution:\n%s",
            users["platform"].value_counts().to_string(),
        )

        return users

    # --------------------------------------------------------

    def generate_sessions(
        self,
        users: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate the Session dataset.

        Each user will have between 1 and 8 sessions.
        Session timestamps are constrained within the
        observation window.
        """

        logger.info("Generating session dataset...")

        sessions: list[dict] = []
        session_counter = 1

        start_date = pd.to_datetime(self.config.start_date)
        window_end = start_date + pd.Timedelta(days=self.config.days)

        for _, user in users.iterrows():

            num_sessions = np.random.randint(
                low=1,
                high=9,
            )

            # Keep all generated sessions within the observation window.
            remaining_days = max(
                (window_end - user["signup_date"]).days,
                1,
            )

            for _ in range(num_sessions):

                offset_days = np.random.randint(
                    low=0,
                    high=remaining_days,
                )

                session_date = (
                    user["signup_date"]
                    + pd.Timedelta(days=offset_days)
                )

                session_time = pd.Timedelta(
                    hours=np.random.randint(9, 22),
                    minutes=np.random.randint(0, 60),
                    seconds=np.random.randint(0, 60),
                )

                sessions.append(
                    {
                        "session_id": f"S{session_counter:09d}",
                        "user_id": user["user_id"],
                        "session_start": session_date + session_time,
                        "platform": user["platform"],
                    }
                )

                session_counter += 1

        sessions = pd.DataFrame(sessions)

        logger.info(
            "Generated %d sessions.",
            len(sessions),
        )

        logger.info(
            "Average sessions per user: %.2f",
            len(sessions) / len(users),
        )

        return sessions

    # --------------------------------------------------------

    def simulate_user_journey(
        self,
        users: pd.DataFrame,
        sessions: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate product analytics events for each session.

        Version 1.0 (Commit 5) models the customer journey as an
        independent per-session state machine, following the
        funnel defined in UserJourney.md:

            landing_page_view
                    │
                    ▼
                  login  (gated every session; see notes below)
                    │
                    ▼
              feature_view
                    │
                    ▼
              upgrade_plan
                    │
                    ▼
            checkout_started
                    │
                    ▼
        payment_success / payment_failed
                    │
                    ▼ (only if payment_success)
        subscription_activated

        Login gating:
            - First session: landing_to_signup -> sign_up ->
              signup_to_login -> login
            - Returning sessions: return_session_login -> login
            Every session independently determines whether a
            login occurs; return visits are NOT guaranteed logins.

        `payment_failed` is a normal funnel branch, not a business
        anomaly. Anomaly injection (e.g. a temporary spike in
        payment failures) is handled separately in
        inject_business_anomalies().

        `sign_up` is a user-level, one-time event and is only
        emitted during each user's first session (ordered by
        session_start).

        Each event carries `platform` (from the session) and
        `country` (from the User Master) to support downstream
        segmentation (e.g. GROUP BY platform / country) without
        requiring a join in Commit 7+.

        Each event also carries `ingestion_timestamp`, which
        defaults to the same value as `event_timestamp`. The two
        fields diverge only when a Late-arriving Events data
        quality issue is injected (Commit 8); see EventSchema.md.

        Design decision: cross-session user state (e.g. whether a
        user has already subscribed) is intentionally NOT tracked
        in this commit. See DecisionLog.md for rationale. As a
        result, the same user may appear to complete the
        subscription funnel more than once across sessions. This
        will be addressed in a future iteration.
        """

        logger.info("Simulating customer journey...")

        # =====================================================
        # Step 1: Prepare sessions
        # =====================================================

        sessions = (
            sessions
            .sort_values(["user_id", "session_start"])
            .copy()
        )

        sessions["session_order"] = (
            sessions
            .groupby("user_id")
            .cumcount()
        )

        sessions["is_first_session"] = (
            sessions["session_order"] == 0
        )

        # Build a fast user_id -> country lookup to avoid merging
        # the full DataFrame inside the loop.
        country_lookup = users.set_index("user_id")["country"].to_dict()

        # =====================================================
        # Step 2: State machine per session
        # =====================================================

        events: list[dict] = []
        event_counter = 1
        checkout_counter = 1

        for _, session in sessions.iterrows():

            user_id = session["user_id"]
            session_id = session["session_id"]
            platform = session["platform"]
            country = country_lookup[user_id]
            current_time = session["session_start"]

            def emit(event_name: str, extra: dict | None = None):
                nonlocal event_counter, current_time
                event = {
                    "event_id": f"E{event_counter:09d}",
                    "session_id": session_id,
                    "user_id": user_id,
                    "event_name": event_name,
                    "event_timestamp": current_time,
                    "ingestion_timestamp": current_time,
                    "platform": platform,
                    "country": country,
                }
                if extra:
                    event.update(extra)
                events.append(event)
                event_counter += 1
                current_time = current_time + pd.Timedelta(
                    seconds=int(np.random.randint(5, 120))
                )

            # ---- landing_page_view: always occurs ----
            emit("landing_page_view")

            # ---- sign_up + login gate ----
            if session["is_first_session"]:
                if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["landing_to_signup"]:
                    continue
                emit("sign_up")

                if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["signup_to_login"]:
                    continue
            else:
                if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["return_session_login"]:
                    continue

            # ---- login: gated for every session ----
            emit("login")

            if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["login_to_feature"]:
                continue

            # ---- feature_view ----
            emit("feature_view")

            if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["feature_to_upgrade"]:
                continue

            # ---- upgrade_plan ----
            emit("upgrade_plan")

            if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["upgrade_to_checkout"]:
                continue

            # ---- checkout_started ----
            checkout_id = f"C{checkout_counter:09d}"
            checkout_counter += 1

            emit("checkout_started", {"checkout_id": checkout_id})

            # ---- payment_success / payment_failed: normal funnel branch ----
            if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["checkout_to_payment_success"]:
                emit("payment_failed", {"checkout_id": checkout_id})
                continue

            emit("payment_success", {"checkout_id": checkout_id})

            if np.random.random() > DEFAULT_FUNNEL_PROBABILITY["payment_success_to_subscription"]:
                continue

            # ---- subscription_activated ----
            emit("subscription_activated", {"checkout_id": checkout_id})

        events = pd.DataFrame(events)

        # =====================================================
        # Step 3: Basic validation
        # =====================================================

        assert events["event_id"].is_unique, (
            "Duplicate event_id detected."
        )

        required_cols = [
            "event_id",
            "session_id",
            "user_id",
            "event_name",
            "event_timestamp",
            "ingestion_timestamp",
            "platform",
            "country",
        ]

        assert events[required_cols].isnull().sum().sum() == 0, (
            "Null values detected in required event fields."
        )

        assert set(events["event_name"].unique()).issubset(
            VALID_EVENT_NAMES
        ), "Invalid event_name detected."

        # =====================================================
        # Step 4: Logging
        # =====================================================

        logger.info(
            "Generated %d events.",
            len(events),
        )

        logger.info(
            "Event distribution:\n%s",
            events["event_name"].value_counts().to_string(),
        )

        return events

    # --------------------------------------------------------
    # Business Anomaly Injection (Commit 7)
    # --------------------------------------------------------

    def inject_business_anomalies(self, events: pd.DataFrame) -> pd.DataFrame:
        """
        Inject the "Payment Gateway Failure" business anomaly, as
        defined in docs/BusinessAnomalyDesign.md.

        On the configured anomaly day, the payment success rate
        drops from the funnel baseline (~91%) to the anomaly target
        (~42%). Only checkouts that were originally successful are
        affected: a portion of them are converted to
        payment_failed, and any corresponding subscription_activated
        event is removed to preserve referential integrity
        (Rule 5b / cardinality from Commit 6).

        Design note: this modifies the simulated business outcome
        in place (event_name is overwritten, some rows are dropped)
        rather than replaying the original event generation
        process. No new rows are added and no columns are changed.
        """

        logger.info("Injecting business anomalies...")

        events = events.copy()

        anomaly_day = BUSINESS_ANOMALY["day"]
        target_success_rate = BUSINESS_ANOMALY["target_payment_success_rate"]
        baseline_success_rate = DEFAULT_FUNNEL_PROBABILITY["checkout_to_payment_success"]

        # Fail fast on misconfiguration: a target rate above baseline
        # is not a valid "failure" scenario and would silently no-op
        # if merely clamped.
        assert target_success_rate <= baseline_success_rate, (
            "BUSINESS_ANOMALY['target_payment_success_rate'] "
            f"({target_success_rate}) must not exceed "
            f"DEFAULT_FUNNEL_PROBABILITY['checkout_to_payment_success'] "
            f"({baseline_success_rate})."
        )

        start_date = pd.to_datetime(self.config.start_date)
        window_start = start_date + pd.Timedelta(days=anomaly_day - 1)
        window_end = window_start + pd.Timedelta(days=1)

        # ---- Identify checkouts whose checkout_started falls in the window ----

        checkout_started_events = events[events["event_name"] == "checkout_started"]
        affected_checkout_ids = (
            checkout_started_events.loc[
                (checkout_started_events["event_timestamp"] >= window_start)
                & (checkout_started_events["event_timestamp"] < window_end),
                "checkout_id",
            ]
            .unique()
            .tolist()
        )

        logger.info(
            "Anomaly window: %s to %s (%d checkouts started).",
            window_start,
            window_end,
            len(affected_checkout_ids),
        )

        if not affected_checkout_ids:
            logger.info("No checkouts found in anomaly window; skipping injection.")
            return events

        # ---- Among affected checkouts, find those that originally succeeded ----

        originally_successful = (
            events.loc[
                (events["event_name"] == "payment_success")
                & (events["checkout_id"].isin(affected_checkout_ids)),
                "checkout_id",
            ]
            .unique()
            .tolist()
        )

        before_success_rate = (
            len(originally_successful) / len(affected_checkout_ids)
            if affected_checkout_ids
            else 0.0
        )

        # ---- Determine how many of them should be flipped to failed ----
        # Only originally-successful checkouts can be flipped
        # (failures stay failures), so the flip probability is
        # derived from the ratio of the target drop.

        flip_probability = 1 - (target_success_rate / baseline_success_rate)

        flip_mask = np.random.random(len(originally_successful)) < flip_probability
        checkouts_to_flip = [
            checkout_id
            for checkout_id, flip in zip(originally_successful, flip_mask)
            if flip
        ]

        logger.info(
            "Flipping %d of %d originally-successful checkouts to payment_failed.",
            len(checkouts_to_flip),
            len(originally_successful),
        )

        # ---- Apply the flip: payment_success -> payment_failed ----

        is_flipped_success = (
            (events["event_name"] == "payment_success")
            & (events["checkout_id"].isin(checkouts_to_flip))
        )
        events.loc[is_flipped_success, "event_name"] = "payment_failed"

        # ---- Remove corresponding subscription_activated events ----
        # A checkout that no longer has payment_success must not
        # retain subscription_activated (would violate Rule 5b).

        is_orphaned_subscription = (
            (events["event_name"] == "subscription_activated")
            & (events["checkout_id"].isin(checkouts_to_flip))
        )
        num_removed = int(is_orphaned_subscription.sum())
        events = events.loc[~is_orphaned_subscription].copy()

        logger.info(
            "Removed %d orphaned subscription_activated event(s).",
            num_removed,
        )

        # ---- Report the resulting success rate within the window ----

        remaining_successful = len(originally_successful) - len(checkouts_to_flip)
        after_success_rate = (
            remaining_successful / len(affected_checkout_ids)
            if affected_checkout_ids
            else 0.0
        )

        logger.info(
            "Payment success rate within anomaly window: %.1f%% -> %.1f%%",
            before_success_rate * 100,
            after_success_rate * 100,
        )

        return events

    # --------------------------------------------------------
    # Data Quality Injection (Commit 8)
    # --------------------------------------------------------

    def inject_data_quality_issues(self, events: pd.DataFrame) -> pd.DataFrame:
        """
        Inject Missing Events, Duplicate Events, and Late-arriving
        Events, as defined in docs/DataQualityInjection.md.

        Injection order: Missing -> Duplicate -> Late Arrival.
        This order matters: Missing Events runs first so dropped
        rows are never eligible for duplication or delay; Duplicate
        Events runs before Late Arrival so new event_ids are
        assigned against a stable baseline.

        All three scenarios are designed to preserve Schema
        Validation (Commit 6/7.5):

        - Missing Events are limited to non-checkout event types,
          so checkout lifecycle integrity (Rule 4 / Rule 5b /
          checkout cardinality) is never broken.
        - Duplicate Events receive a new, unique event_id and an
          offset ingestion_timestamp, so Rule 6 (primary key) and
          Rule 5a (session ordering, which uses event_timestamp)
          both remain satisfied.
        - Late-arriving Events only shift ingestion_timestamp
          forward; event_timestamp (and therefore business
          chronology / Rule 5a) is never touched.
        """

        logger.info("Injecting data quality issues...")

        events = events.copy()
        events_before = len(events)

        # Freshness delay before injection (should be exactly 0,
        # since ingestion_timestamp == event_timestamp in the
        # clean + business-anomaly-injected dataset).
        delay_before = (
            (events["ingestion_timestamp"] - events["event_timestamp"])
            .dt.total_seconds() / 3600
        )
        avg_delay_before = delay_before.mean()

        events, missing_count, missing_candidate_count = self._inject_missing_events(events)
        events, duplicate_count, duplicate_candidate_count = self._inject_duplicate_events(events)
        events, late_count, late_candidate_count = self._inject_late_arrival_events(events)

        events_after = len(events)

        missing_rate = (
            missing_count / missing_candidate_count
            if missing_candidate_count else 0.0
        )
        duplicate_rate = (
            duplicate_count / duplicate_candidate_count
            if duplicate_candidate_count else 0.0
        )
        late_rate = (
            late_count / late_candidate_count
            if late_candidate_count else 0.0
        )

        delay_after = (
            (events["ingestion_timestamp"] - events["event_timestamp"])
            .dt.total_seconds() / 3600
        )
        avg_delay_after = delay_after.mean()

        logger.info(
            "=========================\n"
            "Data Quality Summary\n"
            "=========================\n"
            "Events before injection: %d\n"
            "Events after injection:  %d\n"
            "-------------------------\n"
            "Missing Rate:      %.2f%% (-%d events)\n"
            "Duplicate Rate:    %.2f%% (+%d events)\n"
            "Late Arrival Rate: %.2f%% (%d events delayed)\n"
            "-------------------------\n"
            "Average Ingestion Delay: %.2f hr -> %.2f hr",
            events_before,
            events_after,
            missing_rate * 100,
            missing_count,
            duplicate_rate * 100,
            duplicate_count,
            late_rate * 100,
            late_count,
            avg_delay_before,
            avg_delay_after,
        )

        return events

    # --------------------------------------------------------

    def _inject_missing_events(
        self,
        events: pd.DataFrame,
    ) -> tuple[pd.DataFrame, int, int]:
        """
        Part 1: Missing Events.

        Randomly removes a subset of non-checkout events (per
        DATA_QUALITY['missing_candidates']) to simulate event loss
        during collection or ingestion. checkout_id relationships
        are never touched, so this cannot break Rule 4 / Rule 5b /
        checkout cardinality.

        Returns the updated events, the number of events dropped,
        and the number of candidate events considered.
        """

        candidates = events[
            events["event_name"].isin(DATA_QUALITY["missing_candidates"])
        ]

        missing_rate = DATA_QUALITY["missing_rate"]
        drop_mask = np.random.random(len(candidates)) < missing_rate
        event_ids_to_drop = candidates.loc[drop_mask, "event_id"].tolist()

        events = events[~events["event_id"].isin(event_ids_to_drop)].copy()

        logger.info(
            "Missing Events: dropped %d of %d candidate events (%.1f%% target rate).",
            len(event_ids_to_drop),
            len(candidates),
            missing_rate * 100,
        )

        return events, len(event_ids_to_drop), len(candidates)

    # --------------------------------------------------------

    def _inject_duplicate_events(
        self,
        events: pd.DataFrame,
    ) -> tuple[pd.DataFrame, int, int]:
        """
        Part 2: Duplicate Events.

        Randomly duplicates a subset of events (per
        DATA_QUALITY['duplicate_candidates']) to simulate repeated
        ingestion. Each duplicate receives:
            - a new, unique event_id
            - an ingestion_timestamp offset by 5-20 seconds

        event_timestamp is left unchanged, so Rule 5a (which sorts
        by event_timestamp) is unaffected by the duplication.

        Returns the updated events, the number of duplicates
        created, and the number of candidate events considered.
        """

        candidates = events[
            events["event_name"].isin(DATA_QUALITY["duplicate_candidates"])
        ]

        duplicate_rate = DATA_QUALITY["duplicate_rate"]
        duplicate_mask = np.random.random(len(candidates)) < duplicate_rate
        rows_to_duplicate = candidates.loc[duplicate_mask].copy()

        if rows_to_duplicate.empty:
            logger.info(
                "Duplicate Events: 0 of %d candidate events duplicated (%.1f%% target rate).",
                len(candidates),
                duplicate_rate * 100,
            )
            return events, 0, len(candidates)

        # Assign new, unique event_ids to the duplicated rows.
        existing_max_id = (
            events["event_id"]
            .str.replace("E", "", regex=False)
            .astype(int)
            .max()
        )
        new_ids = [
            f"E{existing_max_id + i + 1:09d}"
            for i in range(len(rows_to_duplicate))
        ]
        rows_to_duplicate["event_id"] = new_ids

        # Offset ingestion_timestamp only, to simulate a second,
        # later ingestion of the same business event.
        offset_seconds = np.random.randint(5, 21, size=len(rows_to_duplicate))
        rows_to_duplicate["ingestion_timestamp"] = (
            rows_to_duplicate["ingestion_timestamp"]
            + pd.to_timedelta(offset_seconds, unit="s")
        )

        events = pd.concat([events, rows_to_duplicate], ignore_index=True)

        logger.info(
            "Duplicate Events: duplicated %d of %d candidate events (%.1f%% target rate).",
            len(rows_to_duplicate),
            len(candidates),
            duplicate_rate * 100,
        )

        return events, len(rows_to_duplicate), len(candidates)

    # --------------------------------------------------------

    def _inject_late_arrival_events(
        self,
        events: pd.DataFrame,
    ) -> tuple[pd.DataFrame, int, int]:
        """
        Part 3: Late-arriving Events.

        Randomly delays the ingestion_timestamp of a subset of
        events (per DATA_QUALITY['late_arrival_candidates']) to
        simulate delayed data platform ingestion.

        event_timestamp is never modified, so business chronology
        and Rule 5a ordering remain fully intact; only Freshness
        (ingestion_timestamp - event_timestamp) is affected.

        Vectorized (no row-wise apply): the random per-row delay
        is generated as a Series aligned to the affected rows, then
        added directly via Series arithmetic.

        Returns the updated events, the number of events delayed,
        and the number of candidate events considered.
        """

        candidates = events[
            events["event_name"].isin(DATA_QUALITY["late_arrival_candidates"])
        ]

        late_rate = DATA_QUALITY["late_arrival_rate"]
        late_mask = np.random.random(len(candidates)) < late_rate
        affected_index = candidates.loc[late_mask].index

        min_hours, max_hours = DATA_QUALITY["late_arrival_hours"]
        delay_hours = np.random.randint(
            min_hours, max_hours + 1, size=len(affected_index)
        )
        delay = pd.to_timedelta(delay_hours, unit="h")
        delay_series = pd.Series(delay.values, index=affected_index)

        events.loc[affected_index, "ingestion_timestamp"] = (
            events.loc[affected_index, "ingestion_timestamp"] + delay_series
        )

        logger.info(
            "Late-arriving Events: delayed %d of %d candidate events "
            "(%.1f%% target rate, %d-%d hour delay window).",
            len(affected_index),
            len(candidates),
            late_rate * 100,
            min_hours,
            max_hours,
        )

        return events, len(affected_index), len(candidates)

    # --------------------------------------------------------
    # Schema Validation (Commit 6, extended in 7.5)
    # --------------------------------------------------------

    def validate_schema(self, events: pd.DataFrame) -> None:
        """
        Validate structural integrity of generated events.

        This validates only the common event schema, as defined in
        docs/SchemaValidation.md. Business metrics (conversion
        rates, distributions) and event-specific additional fields
        (per EventSchema.md) are intentionally out of scope for
        Version 1.0.

        Raises AssertionError immediately on any violation
        (fail-fast principle).
        """

        self._validate_required_columns(events)
        self._validate_data_types(events)
        self._validate_event_names(events)
        self._validate_checkout_relationship(events)
        self._validate_timestamp_order(events)
        self._validate_ingestion_timestamp(events)
        self._validate_checkout_cardinality(events)
        self._validate_primary_key(events)

        logger.info("Schema validation passed: all rules satisfied.")

    # --------------------------------------------------------

    def _validate_required_columns(self, events: pd.DataFrame) -> None:
        """Rule 1: Required Columns."""

        missing_columns = set(self.REQUIRED_COLUMNS) - set(events.columns)
        assert not missing_columns, (
            f"Missing required columns: {missing_columns}"
        )

    # --------------------------------------------------------

    def _validate_data_types(self, events: pd.DataFrame) -> None:
        """
        Rule 2: Data Types.

        `event_timestamp` and `ingestion_timestamp` are validated
        separately as datetime columns; the remaining
        NON_NULLABLE_COLUMNS are validated as string-compatible
        columns.
        """

        for datetime_col in ["event_timestamp", "ingestion_timestamp"]:
            assert pd.api.types.is_datetime64_any_dtype(
                events[datetime_col]
            ), f"{datetime_col} must be datetime64."

        string_columns = [
            col for col in self.NON_NULLABLE_COLUMNS
            if col not in ("event_timestamp", "ingestion_timestamp")
        ]

        for col in string_columns:
            assert pd.api.types.is_object_dtype(events[col]) or (
                events[col].dtype == "string"
            ), f"{col} must be a string-compatible dtype."

        assert events[self.NON_NULLABLE_COLUMNS].isnull().sum().sum() == 0, (
            "Null values detected in non-nullable columns."
        )

    # --------------------------------------------------------

    def _validate_event_names(self, events: pd.DataFrame) -> None:
        """Rule 3: Allowed Event Names."""

        invalid_event_names = (
            set(events["event_name"].unique()) - VALID_EVENT_NAMES
        )
        assert not invalid_event_names, (
            f"Invalid event_name(s) detected: {invalid_event_names}"
        )

    # --------------------------------------------------------

    def _validate_checkout_relationship(self, events: pd.DataFrame) -> None:
        """Rule 4: checkout_id Relationship."""

        checkout_required = events[
            events["event_name"].isin(self.CHECKOUT_ID_REQUIRED_EVENTS)
        ]
        assert checkout_required["checkout_id"].isnull().sum() == 0, (
            "checkout_id missing for checkout-related events."
        )
        assert not (checkout_required["checkout_id"] == "").any(), (
            "checkout_id must not be an empty string."
        )

        checkout_forbidden = events[
            events["event_name"].isin(self.CHECKOUT_ID_FORBIDDEN_EVENTS)
        ]
        assert checkout_forbidden["checkout_id"].notnull().sum() == 0, (
            "checkout_id present on events that must not carry it."
        )

    # --------------------------------------------------------

    def _validate_timestamp_order(self, events: pd.DataFrame) -> None:
        """
        Rule 5: Timestamp Ordering.

        Sorting is performed once across the whole dataset
        (session_id, event_timestamp) rather than per-group, so
        this scales to large datasets without repeated sorts
        inside a Python loop.

        NOTE: this rule is evaluated using `event_timestamp`
        (business time), not `ingestion_timestamp` (platform time).
        This is intentional: Late-arriving Events only shift
        ingestion_timestamp, so business chronology and ordering
        must remain governed by event_timestamp alone.
        """

        order_rank = {
            name: i for i, name in enumerate(self.SESSION_LEVEL_ORDER)
        }
        # payment_failed shares the same rank as payment_success
        order_rank["payment_failed"] = order_rank["payment_success"]

        ordered_events = (
            events
            .assign(event_rank=events["event_name"].map(order_rank))
            .sort_values(["session_id", "event_timestamp"])
        )

        # Fail loudly and specifically if any event_name is missing
        # from SESSION_LEVEL_ORDER / order_rank, rather than letting
        # it silently become NaN and masquerade as a "non-monotonic"
        # ordering failure downstream.
        unknown_rank = ordered_events[ordered_events["event_rank"].isna()]
        assert unknown_rank.empty, (
            "Found event(s) missing from SESSION_LEVEL_ORDER: "
            f"{sorted(unknown_rank['event_name'].unique().tolist())}"
        )

        # ---- Rule 5a: Session-Level Ordering ----

        rank_monotonic = (
            ordered_events
            .groupby("session_id")["event_rank"]
            .apply(lambda ranks: ranks.is_monotonic_increasing)
        )
        assert rank_monotonic.all(), (
            f"Non-monotonic event rank in session(s): "
            f"{rank_monotonic[~rank_monotonic].index.tolist()}"
        )

        time_monotonic = (
            ordered_events
            .groupby("session_id")["event_timestamp"]
            .apply(lambda ts: ts.is_monotonic_increasing)
        )
        assert time_monotonic.all(), (
            f"Timestamps not monotonically increasing in session(s): "
            f"{time_monotonic[~time_monotonic].index.tolist()}"
        )

        # ---- Rule 5b: Checkout-Level Ordering ----
        # Avoids relying on iloc[0] / iloc[-1], so this remains
        # correct even if future anomalies introduce multiple
        # payment_failed retries before a final payment_success.

        checkout_events = events[events["checkout_id"].notnull()]

        for checkout_id, group in checkout_events.groupby("checkout_id"):

            checkout_started_time = group.loc[
                group["event_name"] == "checkout_started",
                "event_timestamp",
            ]
            assert not checkout_started_time.empty, (
                f"checkout_id {checkout_id} has no checkout_started event."
            )

            other_events_time = group.loc[
                group["event_name"] != "checkout_started",
                "event_timestamp",
            ]
            if not other_events_time.empty:
                assert (
                    checkout_started_time.max() <= other_events_time.min()
                ), (
                    f"checkout_started does not precede other checkout "
                    f"events for checkout_id {checkout_id}."
                )

            subscription_time = group.loc[
                group["event_name"] == "subscription_activated",
                "event_timestamp",
            ]
            payment_success_time = group.loc[
                group["event_name"] == "payment_success",
                "event_timestamp",
            ]

            if not subscription_time.empty:
                assert not payment_success_time.empty, (
                    f"subscription_activated found without a "
                    f"payment_success for checkout_id {checkout_id}."
                )
                assert (
                    payment_success_time.max() <= subscription_time.min()
                ), (
                    f"subscription_activated occurs before the latest "
                    f"payment_success for checkout_id {checkout_id}."
                )

    # --------------------------------------------------------

    def _validate_ingestion_timestamp(self, events: pd.DataFrame) -> None:
        """
        New rule (Commit 7.5): ingestion_timestamp must never
        precede event_timestamp.

        Data cannot be ingested by the platform before the
        business event actually occurred. This invariant holds
        both in the clean dataset (where the two are equal) and
        after Late-arriving Events injection (where
        ingestion_timestamp is shifted forward, never backward).
        """

        assert (
            events["ingestion_timestamp"] >= events["event_timestamp"]
        ).all(), (
            "Found event(s) where ingestion_timestamp precedes "
            "event_timestamp."
        )

    # --------------------------------------------------------

    def _validate_checkout_cardinality(self, events: pd.DataFrame) -> None:
        """
        New rule: checkout lifecycle cardinality.

        Each checkout_id should represent a single, well-formed
        checkout attempt:
            - exactly one checkout_started
            - at most one payment_success
            - at most one subscription_activated

        `payment_failed` is intentionally NOT capped here, since
        future anomaly injection may simulate retried payments
        (multiple payment_failed events before an eventual
        payment_success).
        """

        checkout_events = events[events["checkout_id"].notnull()]

        counts = (
            checkout_events
            .groupby("checkout_id")["event_name"]
            .value_counts()
            .unstack(fill_value=0)
        )

        if "checkout_started" in counts.columns:
            invalid_started = counts[counts["checkout_started"] != 1]
            assert invalid_started.empty, (
                f"checkout_id(s) with != 1 checkout_started: "
                f"{invalid_started.index.tolist()}"
            )

        if "payment_success" in counts.columns:
            invalid_payment_success = counts[counts["payment_success"] > 1]
            assert invalid_payment_success.empty, (
                f"checkout_id(s) with > 1 payment_success: "
                f"{invalid_payment_success.index.tolist()}"
            )

        if "subscription_activated" in counts.columns:
            invalid_subscription = counts[counts["subscription_activated"] > 1]
            assert invalid_subscription.empty, (
                f"checkout_id(s) with > 1 subscription_activated: "
                f"{invalid_subscription.index.tolist()}"
            )

    # --------------------------------------------------------

    def _validate_primary_key(self, events: pd.DataFrame) -> None:
        """Rule 6: Primary Key Integrity."""

        assert events["event_id"].is_unique, (
            "Duplicate event_id detected."
        )
        assert events["event_id"].notnull().all(), (
            "Null event_id detected."
        )

    # --------------------------------------------------------

    def export_clean_dataset(self, events):

        self.config.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        events.to_parquet(
            self.config.output_dir / "clean_events.parquet",
            index=False,
        )

    # --------------------------------------------------------

    def export_final_dataset(self, events):

        self.config.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        events.to_parquet(
            self.config.output_dir / "events.parquet",
            index=False,
        )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    generator = SyntheticDataGenerator(CONFIG)

    generator.run()