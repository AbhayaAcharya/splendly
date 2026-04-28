import sqlite3
import os
from flask import g, current_app
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'expense_tracker.db')


def get_db():
    if 'db' not in g:
        path = current_app.config.get('DATABASE', DB_PATH)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER      PRIMARY KEY AUTOINCREMENT,
                name       VARCHAR(100) NOT NULL,
                email      VARCHAR(255) NOT NULL UNIQUE,
                password   VARCHAR(255) NOT NULL,
                created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);

            CREATE TABLE IF NOT EXISTS expenses (
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

            CREATE INDEX IF NOT EXISTS idx_expenses_user_id  ON expenses(user_id);
            CREATE INDEX IF NOT EXISTS idx_expenses_date     ON expenses(user_id, date DESC);
            CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(user_id, category);
        """)
        db.commit()


def seed_db(app):
    with app.app_context():
        db = get_db()
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return
        db.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("password123"))
        )
        user_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.executemany(
            """INSERT INTO expenses (user_id, title, amount, category, date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (user_id, "Grocery run",      85.40,  "Food & Dining",    "2026-04-01", "Weekly shop"),
                (user_id, "Monthly gym",       30.00,  "Health & Medical", "2026-04-05", None),
                (user_id, "Electricity bill", 120.00,  "Utilities",        "2026-04-10", "April bill"),
            ]
        )
        db.commit()


def reset_db(app):
    if not app.config.get('TESTING'):
        raise RuntimeError("reset_db() can only be called when TESTING=True")
    with app.app_context():
        db = get_db()
        db.execute("DROP TABLE IF EXISTS expenses")
        db.execute("DROP TABLE IF EXISTS users")
        db.commit()
    init_db(app)


# --- Query helpers ---

def get_user_by_email(email):
    return get_db().execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()


def create_user(name, email, password):
    db = get_db()
    db.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password))
    )
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def get_expenses_for_user(user_id):
    return get_db().execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC", (user_id,)
    ).fetchall()


def get_expense_by_id(expense_id, user_id):
    return get_db().execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id)
    ).fetchone()
