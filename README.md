# Finance Tracker

A Python finance and inventory tracking project with a Flask web interface, SQLite storage, and a small Tkinter desktop interface for transaction entry.

## Features

- User login with hashed passwords
- Add income and expense transactions
- View saved transactions in the web dashboard
- Store transaction data in SQLite
- Track uniform inventory by category and size
- Update inventory stock quantities
- JSON API endpoints for transactions, summaries, and inventory
- Swagger API documentation for the Flask app
- Desktop Tkinter interface for adding transactions and exporting them to CSV
- Basic reporting script for income and expense totals

## Tech Stack

- Python
- Flask
- SQLite
- Tkinter
- pandas
- matplotlib
- Waitress
- python-dotenv

## Project Structure

```text
Finance Tracker/
+-- auth.py                 # User table setup and password verification
+-- db.py                   # SQLite connection and transaction queries
+-- inventory.py            # Inventory categories, sizes, and stock queries
+-- reports.py              # Basic transaction reporting script
+-- ui.py                   # Tkinter desktop interface
+-- utils.py                # Shared date helper
+-- requirements.txt        # Python dependencies
+-- web/
|   +-- app.py              # Flask web app and API routes
|   +-- static/
|   |   +-- style.css       # Web styling
|   +-- templates/          # HTML templates
+-- finance.db              # Local SQLite database, ignored by git
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The web app also imports `flasgger`, so install it if it is not already available:

```bash
pip install flasgger
```

## Environment Variables

Create a `.env` file in the project root and add a Flask secret key:

```env
FLASK_SECRET_KEY=your-secret-key-here
```

Do not commit `.env`, virtual environments, Python cache files, or local database files. They are already listed in `.gitignore`.

## Create a User

The app uses login authentication. You can create a user from the project root with:

```bash
python -c "from auth import init_auth_db, create_user; init_auth_db(); create_user('admin', 'change-this-password')"
```

Use your own username and password.

## Run the Web App

From the project root:

```bash
python web/app.py
```

Then open:

```text
http://localhost:5000
```

## Run the Desktop App

```bash
python ui.py
```

The desktop app lets you add transactions, view the transaction table, and export records to CSV.

## API Endpoints

Login is required for most API routes.

- `GET /api/transactions` - list transactions
- `GET /api/transactions/<id>` - get one transaction
- `POST /api/transactions` - create a transaction
- `PUT /api/transactions/<id>` - update a transaction
- `DELETE /api/transactions/<id>` - delete a transaction
- `GET /api/summary` - get totals grouped by transaction type
- `GET /api/inventory` - list inventory stock levels
- `POST /api/inventory/update` - update stock for one category and size

Swagger documentation is available through the Flask app.

## Notes

- The local SQLite database is stored as `finance.db`.
- Transaction dates use ISO format, for example `2026-09-02`.
- Inventory stock is tracked for predefined product categories and sizes.
