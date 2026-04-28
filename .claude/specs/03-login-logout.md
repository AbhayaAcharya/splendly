# Spec: Login and Logout

## Overview

This step wires up the `POST /login` route and fully implements `GET /logout`. The login template and `GET /login` route already exist; this feature adds the server-side handler that validates submitted credentials against the stored password hash, opens a session on success, and redirects the user into the app. Logout simply clears the session and redirects to the landing page. Together these two routes complete the authentication loop started by registration in Step 2.

## Depends on

- Step 1 / Spec 03 — Database setup (`database/db.py`, `users` table, `get_user_by_email` helper)
- Step 2 / Spec 02 — Registration (`create_user`, session management pattern)

## Routes

- `POST /login` — Accept login form, verify password, start session, redirect to `/profile` — public
- `GET /logout` — Clear session, redirect to `/` — logged-in (no hard guard needed at this step)

## Database changes

No database changes. All required helpers (`get_user_by_email`) already exist in `database/db.py`.

## Templates

- **No changes:** `templates/login.html` — already extends `base.html`, renders `{{ error }}`, and POSTs to `/login`.

## Files to change

- `app.py` — add `POST` to `/login`'s `methods` list; implement the POST handler using `get_user_by_email` + `check_password_hash`; replace the `/logout` stub with the real implementation; add `check_password_hash` to the `werkzeug.security` import.

## Files to create

- `tests/test_auth.py` — pytest tests covering login and logout flows.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — use `get_user_by_email` from `database/db.py` only
- Parameterised queries only — never interpolate user input into SQL strings
- Passwords verified with `werkzeug.security.check_password_hash` — never roll your own comparison
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- On successful login set `session["user_id"]` to the user's integer id
- On logout call `session.clear()` — do not just pop one key
- Invalid-credential errors must use a generic message ("Invalid email or password") — never reveal whether the email exists
- After successful login redirect to `url_for("profile")`
- After logout redirect to `url_for("landing")`

## Definition of done

- [ ] `GET /login` still returns 200 and renders the form (no regression)
- [ ] Submitting a valid email and password redirects (302) with `session["user_id"]` set to the matching user's id
- [ ] Submitting an incorrect password re-renders the form with "Invalid email or password"
- [ ] Submitting an email that does not exist re-renders the form with "Invalid email or password" (same message — no enumeration)
- [ ] Submitting empty fields re-renders the form with a validation error
- [ ] `GET /logout` clears the session entirely and redirects (302) to the landing page
- [ ] After logout `session["user_id"]` is no longer present in the session
- [ ] `pytest tests/test_auth.py` passes with all tests green
