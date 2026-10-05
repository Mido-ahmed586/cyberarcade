# Database migration — payment checkout fields

If you already ran the app at least once and the `subscriptions` table exists,
you must add the new payment columns manually. SQLAlchemy's
`create_all` only creates missing tables, never adds missing columns.

Run this in pgAdmin → Query Tool against the `cyberarcade` database:

```sql
ALTER TABLE subscriptions
  ADD COLUMN IF NOT EXISTS payment_provider   VARCHAR(30),
  ADD COLUMN IF NOT EXISTS payment_session_id VARCHAR(64) UNIQUE,
  ADD COLUMN IF NOT EXISTS amount_cents       INTEGER,
  ADD COLUMN IF NOT EXISTS currency           VARCHAR(3) DEFAULT 'USD';

CREATE INDEX IF NOT EXISTS ix_subscriptions_payment_session_id
  ON subscriptions (payment_session_id);
```

If `payment_reference` is also missing from your install (it was in the
original schema, so it usually exists), add it too:

```sql
ALTER TABLE subscriptions
  ADD COLUMN IF NOT EXISTS payment_reference VARCHAR(255);
```

That's it — no other tables changed.

## Alternative: drop and recreate

If you don't have any subscriptions you care about, easier is just:

```sql
DROP TABLE IF EXISTS subscriptions CASCADE;
```

Restart the backend with `DEBUG=true` and SQLAlchemy will recreate the table
with the full schema on startup.
