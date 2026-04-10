## 2026-04-10 - Update database optimization using returning
Learning: Single-record database updates in SQLAlchemy 2.0 can be significantly faster by avoiding `commit` followed by `refresh` or select followed by `commit`. Using `update(Model).where(...).values(...).returning(Model)` directly cuts off the database round trips, nearly halving update time.
Action: Implement `returning()` update optimization for `update_job` function in `JobService`.
