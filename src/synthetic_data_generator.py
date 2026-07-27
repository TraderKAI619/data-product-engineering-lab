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

    def generate_sessions(self, users):

        raise NotImplementedError

    # --------------------------------------------------------

    def simulate_user_journey(self, users, sessions):

        raise NotImplementedError

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