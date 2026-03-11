"""Phase 7A — Shared foundations for JobRadar intelligence modules."""

# Import migration modules so their @register_migration decorators execute
# at import time and register with the migration runner.
import backend.phase7a.m1_migrations  # noqa: F401  Module 1: Company Intelligence Registry
import backend.phase7a.m2_migrations  # noqa: F401  Module 2: Search Expansion Engine
import backend.phase7a.m3_migrations  # noqa: F401  Module 3: Validated Source Cache
import backend.phase7a.m4_migrations  # noqa: F401  Module 4: Canonical Jobs Pipeline
import backend.phase7a.m5_migrations  # noqa: F401  Module 5: Application Tracker
