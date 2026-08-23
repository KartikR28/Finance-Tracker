# Finance Tracker — Progress & Roadmap

Started as a personal finance tracker (log income/expenses, view them, see
summary reports). Two interfaces exist in this repo — a working Tkinter
desktop app (`ui.py`) and a Flask web app (`web/app.py`) that we've been
building out feature by feature. It's since grown a second purpose: a
uniform-shop **inventory module** (fixed categories × sizes, stock counts),
kept independent from the income/expense side. **Focus: the Flask web app**,
using `ui.py`/`db.py` as reference for how the data layer works.

## How to use this file
Each step below is small enough to do (and understand) in one sitting. Check a
box when it's done. Add a line or two under "Notes" if something surprised you
or you made a decision worth remembering later.

## Project map — where things live

```
Finance Tracker/
├── finance.db              ← the actual SQLite database file (data lives here)
├── db.py                   ← shared data layer: transactions table
├── inventory.py            ← shared data layer: inventory table (uniform stock)
├── utils.py                ← tiny helper (today_iso())
├── ui.py                   ← Tkinter DESKTOP app (separate interface #1)
├── reports.py              ← standalone CLI script, slightly stale (still uses
│                              a relative DB_PATH — same bug class we fixed in db.py)
├── requirements.txt        ← pinned dependency versions
├── PROGRESS.md              ← this file
└── web/                    ← Flask WEB app (separate interface #2)
    ├── app.py              ← all routes: HTML pages + JSON API + Swagger
    ├── static/style.css    ← CSS (auto light/dark theme)
    └── templates/
        ├── base.html               ← shared layout (nav, page shell)
        ├── index.html              ← "/" — transaction list
        ├── add.html                ← "/add" — add-transaction form
        ├── inventory.html          ← "/inventory" — stock grid
        └── inventory_update.html   ← "/inventory/update" — stock edit form
```

**Core idea:** `db.py` and `inventory.py` don't know or care whether they're
called from Tkinter or Flask — both `ui.py` and `web/app.py` import from them,
so there's exactly one definition of what a "transaction" or "inventory row"
looks like (deliberate — it's why the `type`/`t_type` bug from Step 1 can't
recur).

**How a request flows (example — loading `/`):** browser hits `GET /` →
`index()` in `web/app.py` → calls `fetch_all()` from `db.py` (not defined in
`app.py` itself) → `SELECT * FROM transactions` → rows passed into
`render_template('index.html', transactions=...)` → `index.html` extends
`base.html` for the nav/shell and loops over rows with `{% for %}`. Adding a
transaction, viewing/updating inventory, and the `/api/...` JSON routes all
follow the same shape: route function → `db.py`/`inventory.py` function →
template (or `jsonify(...)` for the API).

Where to look when something breaks: wrong data → check `db.py`/`inventory.py`
first (single source of truth); wrong page markup → the specific file in
`web/templates/`; route/behavior on submit → `web/app.py`; "why did we do it
this way" → the Notes log below, in order.

## Roadmap

- [x] **Step 1 — Fix the foundations**
  - Pin dependencies in `requirements.txt` (Flask, pandas, matplotlib) — matched
    to what's already installed in `.venv`
  - Fix column name mismatch: `web/app.py` was inserting into a column called
    `type`, but the actual schema (`db.py`) calls it `t_type`
  - Decided: web app now imports and reuses `db.py`'s `get_conn`,
    `insert_transaction`, `fetch_all`, `init_db` instead of duplicating raw
    `sqlite3` calls — this is *why* the bug happened in the first place (two
    copies of the schema knowledge, only one got updated)

- [x] **Step 2 — `templates/` and the home page (`/`)**
  - Created `web/templates/base.html` (shared layout: nav, basic CSS)
  - Created `web/templates/index.html` (table of transactions, extends base)
  - Ran the app, confirmed `/` returns 200 and lists real rows from `finance.db`

- [x] **Step 3 — Add transaction form (`/add`)**
  - Created `web/templates/add.html` (form: type, category, amount, date, note)
  - Tightened the `/add` route: strips input, validates category is non-empty
    and amount is numeric, re-renders the form with an inline error instead
    of crashing (no flash messages yet — that's Step 5 polish)
  - Verified end-to-end via Flask's test client: valid POST redirects and the
    new row shows up on `/`; empty category and non-numeric amount both show
    the error message instead of a 500

- [x] **Step 3.5 — Round out `db.py`'s functions (data layer, no UI yet)**
  - Added `update_transaction(id, ...)` — overwrite one row by id
  - Added `delete_transaction(id)` — remove one row by id
  - Added `get_summary()` — `SUM(amount) GROUP BY t_type` in plain SQL, returns
    a dict like `{"Income": 50000.0, "Expense": 2050.0}`; this is the shared
    home for totals logic instead of each interface recomputing it with pandas
  - Verified all three with a disposable test row (insert → update → confirm
    summary changed → delete → confirm summary returned to original values)
  - Added `fetch_one(id)` — fetches a single row by id (`None` if it doesn't
    exist), needed to pre-fill an Edit form with a transaction's current
    values. Verified: real id returns the row, missing id returns `None`.
  - Not wired into `ui.py` / `web/app.py` yet — delete/edit buttons come in
    Step 5, `get_summary()` gets used by `/report` in Step 4

- [ ] **Step 4 — Report page (`/report`)**
  - Create `web/templates/report.html`
  - Use `db.get_summary()` for the totals table; keep pandas only for the
    per-category chart (that's presentation, not core data logic)
  - Render the base64 chart image already generated in `app.py`
  - Handle the empty-data case (no transactions yet) without crashing

- [ ] **Step 5 — Polish**
  - Basic styling (one shared CSS file)
  - Flash messages for success/validation errors instead of silent redirects
  - Delete/edit a transaction from the web UI

- [ ] **Step 6 — Stretch goals** (pick if/when relevant)
  - Filter transactions by date range / category
  - Monthly summary view
  - Auth (only if this becomes multi-user / gets deployed somewhere)

- [x] **UI polish pass (ahead of Step 4/5)**
  - Added `web/static/style.css`: CSS variables for colors, with a
    `prefers-color-scheme: dark` override block so the app auto-matches the
    visitor's OS light/dark setting — no toggle needed
  - Rebuilt `base.html` around a centered `.page` container, a pill-style
    nav, and a `.card` surface for content instead of raw unstyled HTML
  - `index.html`: transactions table now has color-coded Income/Expense
    badges and right-aligned, 2-decimal amounts
  - `add.html`: form fields and submit button restyled to match
  - report.html still doesn't exist yet — that's still Step 4

- [x] **Inventory management module (new direction, alongside transactions)**
  - New `inventory.py` (root, parallel to `db.py`, reuses its `get_conn`):
    `CATEGORIES` (14 fixed uniform item names), `SIZES` (numeric 22-40),
    `init_inventory_db()`, `seed_categories()` (idempotent, `INSERT OR
    IGNORE`), `fetch_inventory()`, `get_stock(category, size)`,
    `update_stock(category, size, quantity)` — sets the total directly
    (no movement history), independent of the `transactions` table
  - `web/app.py`: `/inventory` (grid view, category rows × size columns),
    `/inventory/update` (form, validates category/size/quantity), plus
    matching `/api/inventory` (GET) and `/api/inventory/update` (POST) so
    it's testable via Swagger the same way transactions are
  - New templates: `inventory.html`, `inventory_update.html`; added
    "Inventory" tab to `base.html` nav
  - Verified end-to-end: seeded 14 × 10 = 140 rows at quantity 0, tested a
    valid update, all 3 validation error paths (bad category/size/quantity),
    and the JSON API — then reset the two test-touched rows back to 0

- [x] **Show transaction `id` on the home page**
  - `index.html` never displayed `id`, so there was no way to know which row
    to target for update/delete without going through Swagger or a terminal
    script. Added an `ID` column (muted color, first column) to the table in
    `web/templates/index.html`. Verified `/` still renders and includes it.
  - Deleting a transaction right now is still manual either via
    `DELETE /api/transactions/{id}` in Swagger UI, or
    `python -c "import db; db.delete_transaction(<id>)"` from the terminal —
    no Delete button in the web UI yet (that's still Step 5).

## Notes
_(running log — append short dated notes here as decisions get made or bugs get found)_

- 2026-07-26: Confirmed desktop app works; Flask app has no templates and a
  schema mismatch bug (`type` vs `t_type`). Decided to build out the web app
  first since it needs the most foundational work.
- 2026-07-26: Step 1 done. `web/app.py` now does
  `sys.path.insert(0, "..")` + `from db import ...` so it shares one schema
  definition with the desktop app. Verified installed versions via `.venv`
  (Flask 3.1.2, pandas 2.3.3, matplotlib 3.10.7) and pinned those in
  `requirements.txt`. Templates still don't exist yet — running the app now
  will hit `TemplateNotFound` on every route, that's Step 2.
- 2026-07-27: Step 2 done — added `web/templates/base.html` (shared layout
  with `{% block %}`s) and `index.html` (extends base, loops over
  transactions with `{% for %}`). While testing, found a second, more
  fundamental bug: `db.py`'s `DB_PATH = "finance.db"` was a *relative* path,
  so running Flask from `web/` silently created a brand-new empty
  `web/finance.db` instead of using the real one (SQLite creates missing
  files rather than erroring). Fixed by making `DB_PATH` absolute, anchored
  to `db.py`'s own location via `__file__` — now it doesn't matter which
  directory you launch Python from. Verified `/` returns 200 with real data
  via Flask's test client.
- 2026-07-28: Added a JSON REST API layer over db.py (`/api/transactions`
  GET/POST, `/api/transactions/<id>` GET/PUT/DELETE, `/api/summary`) plus
  `flasgger` for an interactive Swagger UI at `/apidocs/` — lets us test
  db.py functions from a browser instead of writing a script each time.
  Hit two real bugs while wiring it up, both worth remembering:
  (1) a stale Flask dev server from an earlier test hadn't actually died and
  was silently squatting on port 5057, so a newly-started server appeared to
  ignore code changes — killed by PID via `Stop-Process`, not just
  TaskStop/Ctrl+C, to be sure it's actually gone;
  (2) `/apispec_1.json` 500'd because a route docstring's YAML description
  contained a raw `{"Income": ...}` JSON example — the unquoted `{`/`:`
  characters are YAML flow-mapping syntax, so they broke the parser. Fixed
  by quoting that description string. General lesson: don't put
  colons/braces unquoted inside a YAML plain-scalar string.
- 2026-07-27: Step 3 done — `add.html` form + validation in the `/add` route.
  Tested by actually POSTing a labeled test row (`__TEST_STEP3__`) through
  the running app, confirming it appeared on `/`, then deleting just that
  row from `finance.db` afterward so real data stayed untouched (4 rows
  remain, as before).
