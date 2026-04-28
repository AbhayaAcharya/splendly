# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** is a Flask-based personal expense tracking web app. It is a structured learning project with incremental implementation steps (Steps 1–9). Many routes and the database module are stubs waiting to be implemented.

## Commands

```bash
# Install dependencies (first time)
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the dev server (http://localhost:5001)
python app.py

# Run tests
pytest

# Run a single test file
pytest tests/test_auth.py
```

## Architecture

```
app.py          — Flask app; all routes defined here
database/db.py  — SQLite module (stub); must expose get_db(), init_db(), seed_db()
templates/      — Jinja2 templates; base.html is the master layout
static/css/     — style.css is the complete design system (CSS variables, components)
static/js/      — main.js is a stub for frontend logic
```

**Data flow:** `app.py` routes render Jinja2 templates from `templates/`. The database layer (`database/db.py`) will be imported into `app.py` once implemented. SQLite file is `expense_tracker.db` (git-ignored).

## Implementation Steps (student guide)

| Step | Feature |
|------|---------|
| 1 | `database/db.py` — `get_db()`, `init_db()`, `seed_db()` |
| 2 | Database schema — users and expenses tables |
| 3 | Auth — `/logout` (session management) |
| 4 | `/profile` page |
| 7 | `/expenses/add` |
| 8 | `/expenses/<id>/edit` |
| 9 | `/expenses/<id>/delete` |

## Design System

CSS custom properties are defined at the top of `static/css/style.css`. Key tokens:
- Colors: `--ink` (#0f0f0f), `--paper` (#f7f6f3), `--accent` (#1a472a), `--accent-2` (#c17f24), `--danger` (#c0392b)
- Fonts: DM Serif Display (headings), DM Sans (body) — loaded via Google Fonts in `base.html`
- Max content width: 1200px; auth forms: 440px
