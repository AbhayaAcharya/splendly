# Spec: Database Setup — Enhanced (v3)

> Merges and supersedes `01-database-setup.md` (sqlite3 implementation guide) and
> `02-database-setup.md` (full schema reference with indexes, models, security notes).
> Date: 2026-04-28

---

## Goal

Extend the working `database/db.py` SQLite layer with:
1. Richer schema — `updated_at` on both tables, `notes` + `CHECK` constraint on `expenses`, indexes
2. Configurable `DB_PATH` via Flask app config (enables in-memory DB for tests)
3. `close_db()` extracted into `db.py` (currently inlined in `app.py`)
4. `reset_db(app)` — test-only utility for a clean slate between test runs
5. Query helper functions so route handlers never write raw SQL
6. `SECRET_KEY` wired into `app.config` (required for session auth in later steps)
7. `tests/conftest.py` — pytest fixtures backed by an in-memory DB

---

## Files

| File | Change |
|------|--------|
| `database/db.py` | Richer schema, helpers, `close_db`, `reset_db`, configurable path |
| `app.py` | Import `close_db` from `db.py`, remove inline teardown, add `SECRET_KEY` |
| `tests/conftest.py` | New — pytest fixtures with in-memory DB |

---

## Schema

### `users` table

| Column          | Type         | Constraints                             | Notes |
|-----------------|--------------|-----------------------------------------|-------|
| `id`            | INTEGER      | PRIMARY KEY AUTOINCREMENT               | |
| `name`          | VARCHAR(100) | NOT NULL                                | Display name |
| `email`         | VARCHAR(255) | NOT NULL, UNIQUE                        | Login identifier |
| `password`      | VARCHAR(255) | NOT NULL                                | Store hashed value — never plaintext |
| `created_at`    | DATETIME     | NOT NULL, DEFAULT CURRENT_TIMESTAMP     | |
| `updated_at`    | DATETIME     | NOT NULL, DEFAULT CURRENT_TIMESTAMP     | Update on every profile write |

**Indexes:**
- `UNIQUE INDEX idx_users_email ON users(email)`

---

### `expenses` table

| Column       | Type          | Constraints                                            | Notes |
|--------------|---------------|--------------------------------------------------------|-------|
| `id`         | INTEGER       | PRIMARY KEY AUTOINCREMENT                              | |
| `user_id`    | INTEGER       | NOT NULL, FOREIGN KEY → `users(id)` ON DELETE CASCADE  | |
| `title`      | VARCHAR(255)  | NOT NULL                                               | Short description |
| `amount`     | NUMERIC(10,2) | NOT NULL, CHECK (amount > 0)                           | Positive monetary value |
| `category`   | VARCHAR(100)  | NOT NULL, DEFAULT 'Uncategorized'                      | See category list below |
| `date`       | DATE          | NOT NULL, DEFAULT CURRENT_DATE                         | ISO format: YYYY-MM-DD |
| `notes`      | TEXT          | NULLABLE                                               | Optional free-text detail |
| `created_at` | DATETIME      | NOT NULL, DEFAULT CURRENT_TIMESTAMP                    | |
| `updated_at` | DATETIME      | NOT NULL, DEFAULT CURRENT_TIMESTAMP                    | Update on every expense write |

**Indexes:**
- `INDEX idx_expenses_user_id ON expenses(user_id)` — fast per-user lookup
- `INDEX idx_expenses_date ON expenses(user_id, date DESC)` — date-sorted listings
- `INDEX idx_expenses_category ON expenses(user_id, category)` — category filtering

**Foreign Key:**
```sql
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

---

## Entity-Relationship Diagram

```
┌─────────────────────┐          ┌──────────────────────────┐
│        users        │          │         expenses         │
├─────────────────────┤          ├──────────────────────────┤
│ id          (PK)    │◄────┐    │ id           (PK)        │
│ name                │     └────│ user_id      (FK→users)  │
│ email               │  1  :  N │ title                    │
│ password            │          │ amount                   │
│ created_at          │          │ category                 │
│ updated_at          │          │ date                     │
└─────────────────────┘          │ notes                    │
                                 │ created_at               │
                                 │ updated_at               │
                                 └──────────────────────────┘
```

---

## Raw SQL: Create Statements

```sql
CREATE TABLE users (
    id         INTEGER      PRIMARY KEY AUTOINCREMENT,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(255) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_users_email ON users(email);


CREATE TABLE expenses (
    id         INTEGER       PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      VARCHAR(255)  NOT NULL,
    amount     NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    category   VARCHAR(100)  NOT NULL DEFAULT 'Uncategorized',
    date       DATE          NOT NULL DEFAULT CURRENT_DATE,
    notes      TEXT,
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_expenses_user_id  ON expenses(user_id);
CREATE INDEX idx_expenses_date     ON expenses(user_id, date DESC);
CREATE INDEX idx_expenses_category ON expenses(user_id, category);
```

---

## Functions in `database/db.py`

### Existing — updated

#### `get_db() → sqlite3.Connection`
- Resolve path from `current_app.config['DATABASE']` when set; fall back to module-level `DB_PATH`.
- Stores on `g`, sets `row_factory = sqlite3.Row`, enables `PRAGMA foreign_keys = ON`.

#### `init_db(app) → None`
- Updated CREATE statements include `updated_at`, `notes`, `CHECK (amount > 0)`, and all indexes.

#### `seed_db(app) → None`
- Idempotent (early return if users table is non-empty).
- Populate `notes` on sample rows; use `generate_password_hash` for password.

### New functions

#### `close_db(error=None) → None`
- Pops `'db'` from `g` and closes the connection.
- Replaces the inline teardown currently in `app.py`.

#### `reset_db(app) → None`
- Drops `expenses` then `users`, then calls `init_db(app)`.
- Raises `RuntimeError` unless `app.config['TESTING'] is True`.

#### `get_user_by_email(email: str) → sqlite3.Row | None`
- `SELECT * FROM users WHERE email = ?`

#### `get_expenses_for_user(user_id: int) → list[sqlite3.Row]`
- `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC`

#### `get_expense_by_id(expense_id: int, user_id: int) → sqlite3.Row | None`
- `SELECT * FROM expenses WHERE id = ? AND user_id = ?`
- Scopes to `user_id` — prevents IDOR on edit/delete routes.

---

## Integration in `app.py`

```python
from flask import Flask, render_template, g
from database.db import init_db, seed_db, close_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-change-in-production'

init_db(app)
seed_db(app)

app.teardown_appcontext(close_db)
```

Remove the old inline `close_db` function from `app.py`.

---

## Test Support — `tests/conftest.py`

```python
import pytest
from app import app as flask_app
from database.db import init_db, seed_db, reset_db

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['DATABASE'] = ':memory:'
    init_db(flask_app)
    seed_db(flask_app)
    yield flask_app
    reset_db(flask_app)

@pytest.fixture
def client(app):
    return app.test_client()
```

---

## Suggested Category Values

Seed as a static list in the app (no separate DB table needed at this stage):

- Food & Dining
- Transport
- Housing / Rent
- Utilities
- Health & Medical
- Entertainment
- Shopping
- Travel
- Education
- Uncategorized

---

## Acceptance Criteria

- [ ] Both tables created with `updated_at`, indexes, and `CHECK (amount > 0)`.
- [ ] `expenses` table has `notes` column (nullable).
- [ ] `get_db()` uses `app.config['DATABASE']` when set — in-memory DB works in tests.
- [ ] `close_db` imported from `db.py`; no inline teardown in `app.py`.
- [ ] `reset_db()` raises `RuntimeError` when `TESTING` is not `True`.
- [ ] `get_expense_by_id()` returns `None` when `user_id` doesn't match (IDOR guard).
- [ ] `pytest` passes with in-memory DB — no `expense_tracker.db` written during tests.

---

## Security Notes

- **Never store plaintext passwords.** Use `werkzeug.security.generate_password_hash`.
- **Always scope expense queries to `user_id`.** Never trust the `<id>` URL param alone — `get_expense_by_id` enforces this.
- Use Flask session to track the logged-in `user_id` (implemented in Step 3).
- `SECRET_KEY` must be set before any session work.

---

## Future Extensions (out of scope now)

| Feature              | What to add                                              |
|----------------------|----------------------------------------------------------|
| Multiple currencies  | `currency VARCHAR(3)` on `expenses`                      |
| Recurring expenses   | `recurrence_rule VARCHAR(50)` on `expenses`              |
| Expense attachments  | New `attachments` table with FK to `expenses`            |
| Tags / labels        | `tags` + `expense_tags` junction table                   |
| Budget limits        | New `budgets` table with `user_id`, `category`, `limit`  |
| Soft delete          | `deleted_at DATETIME NULL` on `expenses`                 |
