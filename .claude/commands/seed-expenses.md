---
description: Seed realistic dummy expenses for a user — usage: seed-expenses <count> <months>
allowed-tools: Read, Bash(python3:*)
---

Parse the arguments from: $ARGUMENTS

- First argument  → **count**  (total number of expenses to create; default 50)
- Second argument → **months** (how many past months to spread them across; default 3)

Example: `seed-expenses 150 6` → insert 150 expenses for 1 user, spread randomly across the last 6 months.

---

## Steps

### 1 — Read the schema
Read `database/db.py` to confirm:
- The `expenses` table columns: `user_id`, `title`, `amount`, `category`, `date`, `notes`
- The `DB_PATH` constant so the script connects to the correct file without Flask context

### 2 — Write and run a self-contained Python script via Bash

The script must do the following in order:

**A. Connect to the database directly**
```python
import sqlite3, os, random, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expense_tracker.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")
```

**B. Pick the target user**
- `SELECT id, name, email FROM users ORDER BY id ASC LIMIT 1`
- If no rows returned, print and exit:
  ```
  ✗ No users found. Run /seed-user first, then retry.
  ```
- Otherwise print: `Seeding expenses for: <name> (<email>) [id=<id>]`

**C. Build expenses using exactly these categories**

Use only the categories defined in `03-database-setup.md` (specs). No other values are allowed:

| Category | Typical titles | Amount range |
|---|---|---|
| `Food & Dining` | Grocery run, Swiggy order, Zomato delivery, Restaurant dinner, Coffee & snacks, Bakery visit, Chai & breakfast, Weekly groceries, Supermarket run | 80 – 1 200 |
| `Transport` | Ola cab, Uber ride, Metro card recharge, Petrol fill-up, Auto rickshaw, Bus pass renewal, Toll charges, Cab to office, Airport taxi | 40 – 2 500 |
| `Housing / Rent` | Monthly rent, Maintenance charges, Society fee, Parking charges, House cleaning service | 2 000 – 25 000 |
| `Utilities` | Electricity bill, Water bill, Mobile recharge, Broadband plan, Gas cylinder, Piped gas bill, DTH recharge | 150 – 3 500 |
| `Health & Medical` | Pharmacy purchase, Doctor consultation, Lab tests, Gym membership, Health insurance premium, Dentist visit, Eye checkup | 100 – 5 000 |
| `Entertainment` | Movie tickets, Netflix subscription, Spotify premium, BookMyShow, Gaming top-up, OTT subscription, Concert tickets | 100 – 2 000 |
| `Shopping` | Clothing purchase, Amazon order, Flipkart order, Stationery, Household supplies, Electronics accessory, Home decor | 200 – 8 000 |
| `Travel` | Flight booking, Train ticket, Hotel stay, Holiday package, Cab to airport, Travel insurance, Visa fee | 500 – 25 000 |
| `Education` | Online course, Book purchase, Udemy course, Skill workshop, Exam registration fee, Coaching class fee | 200 – 15 000 |
| `Uncategorized` | Miscellaneous expense, ATM withdrawal, Bank charges, Gift, Donation, Subscription renewal | 50 – 3 000 |

**Category weighting** (so distribution looks realistic, not uniform):
```python
CATEGORIES = [
    "Food & Dining",      # weight 30
    "Transport",          # weight 20
    "Utilities",          # weight 10
    "Health & Medical",   # weight 8
    "Shopping",           # weight 8
    "Entertainment",      # weight 7
    "Housing / Rent",     # weight 5
    "Travel",             # weight 4
    "Education",          # weight 4
    "Uncategorized",      # weight 4
]
WEIGHTS = [30, 20, 10, 8, 8, 7, 5, 4, 4, 4]
```
Use `random.choices(CATEGORIES, weights=WEIGHTS, k=count)` to pick one category per expense.

**For each expense row:**
- Pick a title randomly from that category's title list
- Pick amount with `round(random.uniform(low, high), 2)`
- Add a short realistic note for ~60% of rows; use `None` for the rest
- Pick a date (see step D)

**D. Spread dates across the past `<months>` months**
```python
today = datetime.date.today()
# First day of the month that is <months> ago
start = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
# repeat <months>-1 more times to go back far enough
for _ in range(months - 1):
    start = (start - datetime.timedelta(days=1)).replace(day=1)
end = today - datetime.timedelta(days=1)  # yesterday — never today
total_days = (end - start).days
```
Pick each date with `start + datetime.timedelta(days=random.randint(0, total_days))`.

**E. Insert in bulk**
```python
conn.executemany(
    """INSERT INTO expenses (user_id, title, amount, category, date, notes)
       VALUES (?, ?, ?, ?, ?, ?)""",
    rows
)
conn.commit()
```

**F. Print a summary**
```
✓ Inserted 150 expenses for Rahul Sharma (rahul.sharma91@gmail.com)
  Date range : 2025-11-01 → 2026-04-27
  Categories : Food & Dining (45), Transport (29), Utilities (14), ...
  Total spend: ₹1,23,450.75
```

### 3 — Verify with a DB sanity check
```python
row = conn.execute(
    "SELECT COUNT(*), SUM(amount) FROM expenses WHERE user_id = ?", (user_id,)
).fetchone()
print(f"DB check → total rows for user: {row[0]}, total amount: ₹{row[1]:,.2f}")
```

### 4 — Close the connection
```python
conn.close()
```

---

## Constraints
- Use **only** the 10 categories listed in this file — no others
- Never delete existing expenses — always append
- `amount` must be > 0 and stored as `NUMERIC(10,2)`
- `date` must be a past date — never today or in the future
- `user_id` must exist in the `users` table (FK enforced)
