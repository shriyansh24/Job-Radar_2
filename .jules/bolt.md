## 2026-04-08 - Optimize Single-Record Database Updates
Learning: In SQLAlchemy 2.0, single-record database updates that fetch, update, commit, and refresh can require 3 database roundtrips. Using `update(Model).where(...).values(...).returning(Model)` directly reduces this to 1 database roundtrip.
Action: Prefer using the `update().returning()` pattern over the `select` -> `setattr` -> `commit` -> `refresh` pattern for simple updates to minimize database roundtrips.
