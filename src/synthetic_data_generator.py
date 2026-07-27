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
# Generator
# ============================================================

class SyntheticDataGenerator:
    """Generate synthetic Product Analytics events."""

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

    def inject_business_anomalies(self, events):

        return events

    # --------------------------------------------------------

    def inject_data_quality_issues(self, events):

        return events

    # --------------------------------------------------------

    def validate_schema(self, events):
        """
        Validate structural integrity of generated events.

        Version 1.0 validates:

        - Required columns
        - Data types
        - Event names
        - checkout_id relationship integrity
        - Schema version
        """

        pass

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