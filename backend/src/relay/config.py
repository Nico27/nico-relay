"""Runtime configuration, read once from the environment."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_DATABASE_URL = "postgresql://relay:relay@localhost:5432/relay"


@dataclass(frozen=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    baseline_weeks: int = 8

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        return cls(
            database_url=env.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            baseline_weeks=int(env.get("BASELINE_WEEKS", "8")),
        )
