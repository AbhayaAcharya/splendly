# Spec: Registration

## Overview

This step wires up the `POST /register` route so new users can actually create an account. The GET route and `register.html` template already exist; this feature adds the server-side handler that validates the submitted form, checks for duplicate emails, hashes the password, inserts the user row, opens a session, and redirects into the app. It is the foundation every subsequent logged-in feature depends on.

## Depends on

- Step 1 / Spec 03 — Database setup (`database/db.py`, `users` table, `get_user_by_email` helper)

## Routes

- `POST /register` — Accept registration form, create user, start session, redirect — public

## Database changes

No database changes. The `users` table and all required indexes are already created by `init_db()` in `database/db.py`. One new query helper is needed:

```
create_user(name, email, password) → int   — INSERT INTO users … RETURNING last_insert_rowid()
```

## Templates

- **Modify:** `templates/register.html` — already renders `{{ error }}`; no changes needed unless flash-message support is added

## Files to change

- `app.py` — extend `/register` to handle `POST`; add `request`, `session`, `redirect`, `url_for` to Flask imports; import `create_user` from `database.db`
- `database/db.py` — add `create_user(name, email, password)` helper

## Files to create

- `tests/test_registration.py` — pytest tests covering the registration flow

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — use `sqlite3` via `get_db()` only
- Parameterised queries only — never interpolate user input into SQL strings
- Passwords hashed with `werkzeug.security.generate_password_hash` inside `create_user` — never in the route
- Normalize email to lowercase before the duplicate check and before storage
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `session["user_id"]` must be set to the new user's integer id after a successful registration

## Definition of done

- [ ] `GET /register` still returns 200 and renders the form (no regression)
- [ ] Submitting a valid form creates a row in `users` with a bcrypt-hashed password (verify with `sqlite3 expense_tracker.db "SELECT password FROM users WHERE email='test@example.com'"`)
- [ ] After successful registration the browser is redirected (302) and `session["user_id"]` is set
- [ ] Submitting an email that already exists re-renders the form with the text "already exists"
- [ ] Submitting a password shorter than 8 characters re-renders the form with "8 characters"
- [ ] Submitting empty fields re-renders the form with "required"
- [ ] `DAVE@EXAMPLE.COM` and `dave@example.com` are treated as the same email (duplicate detected)
- [ ] `pytest tests/test_registration.py` passes with all tests green
