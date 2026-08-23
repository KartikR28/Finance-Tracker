import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from functools import wraps

from flask import Flask, render_template, request, redirect, jsonify, session
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
import io, base64
from flasgger import Swagger
from dotenv import load_dotenv
load_dotenv()


from db import (
    get_conn, insert_transaction, fetch_all, fetch_one,
    update_transaction, delete_transaction, get_summary, init_db,
)
from inventory import (
    CATEGORIES, SIZES, init_inventory_db, seed_categories,
    fetch_inventory, get_stock, update_stock,
)
from auth import init_auth_db, verify_user

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config['SWAGGER'] = {'title': 'Finance Tracker API', 'uiversion': 3}
Swagger(app)

init_db()
init_inventory_db()
seed_categories()
init_auth_db()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect('/login')
        return view(*args, **kwargs)
    return wrapped

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = verify_user(username, password)
        if user is None:
            error = "Invalid username or password."
        else:
            session['user_id'] = user['id']
            return redirect('/')
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
@login_required
def index():
    transactions = fetch_all()
    return render_template('index.html', transactions=transactions)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    today = date.today().isoformat()
    if request.method == 'POST':
        t_type = request.form.get('type', '')
        category = request.form.get('category', '').strip()
        amount_text = request.form.get('amount', '').strip()
        note = request.form.get('note', '').strip()
        date_text = request.form.get('date', '').strip() or today

        if not category or not amount_text:
            return render_template('add.html', error="Category and amount are required.", today=today)
        try:
            amount = float(amount_text)
        except ValueError:
            return render_template('add.html', error="Amount must be a number.", today=today)

        insert_transaction(t_type, category, amount, date_text, note)
        return redirect('/')
    return render_template('add.html', today=today)

@app.route('/report')
@login_required
def report():
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM transactions", conn)
    summary = df.groupby('t_type')['amount'].sum()

    plt.figure(figsize=(5,4))
    df.groupby(['t_type','category'])['amount'].sum().plot(kind='bar')
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return render_template('report.html', summary=summary.to_dict(), graph_url=graph_url)

@app.route('/inventory')
@login_required
def inventory_view():
    rows = fetch_inventory()
    stock = {(r['category'], r['size']): r['quantity'] for r in rows}
    table = [
        {
            'category': category,
            'cells': [stock.get((category, size), 0) for size in SIZES],
        }
        for category in CATEGORIES
    ]
    return render_template('inventory.html', sizes=SIZES, table=table)

@app.route('/inventory/update', methods=['GET', 'POST'])
@login_required
def inventory_update():
    error = None
    if request.method == 'POST':
        category = request.form.get('category', '')
        size_text = request.form.get('size', '')
        quantity_text = request.form.get('quantity', '').strip()

        if category not in CATEGORIES:
            error = "Pick a valid category."
        elif not size_text.isdigit() or int(size_text) not in SIZES:
            error = "Pick a valid size."
        elif not quantity_text.isdigit():
            error = "Quantity must be a whole number (0 or more)."
        else:
            update_stock(category, int(size_text), int(quantity_text))
            return redirect('/inventory')

    return render_template('inventory_update.html', categories=CATEGORIES, sizes=SIZES, error=error)

@app.route('/api/transactions', methods=['GET'])
@login_required
def api_list_transactions():
    """List all transactions
    ---
    responses:
      200:
        description: All transactions, newest date first
    """
    return jsonify([dict(row) for row in fetch_all()])

@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
@login_required
def api_get_transaction(transaction_id):
    """Get one transaction by id
    ---
    parameters:
      - name: transaction_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: The transaction
      404:
        description: No transaction with that id
    """
    row = fetch_one(transaction_id)
    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))

@app.route('/api/transactions', methods=['POST'])
@login_required
def api_create_transaction():
    """Create a transaction
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [t_type, category, amount]
          properties:
            t_type: {type: string, example: Expense}
            category: {type: string, example: groceries}
            amount: {type: number, example: 500}
            date: {type: string, example: "2026-07-28"}
            note: {type: string, example: ""}
    responses:
      201:
        description: Created
    """
    data = request.get_json(force=True)
    insert_transaction(
        data['t_type'], data['category'], float(data['amount']),
        data.get('date') or date.today().isoformat(), data.get('note', ''),
    )
    return jsonify({"status": "created"}), 201

@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
def api_update_transaction(transaction_id):
    """Update a transaction by id
    ---
    parameters:
      - name: transaction_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [t_type, category, amount, date]
          properties:
            t_type: {type: string}
            category: {type: string}
            amount: {type: number}
            date: {type: string}
            note: {type: string}
    responses:
      200:
        description: Updated
      404:
        description: No transaction with that id
    """
    if fetch_one(transaction_id) is None:
        return jsonify({"error": "not found"}), 404
    data = request.get_json(force=True)
    update_transaction(
        transaction_id, data['t_type'], data['category'],
        float(data['amount']), data['date'], data.get('note', ''),
    )
    return jsonify({"status": "updated"})

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def api_delete_transaction(transaction_id):
    """Delete a transaction by id
    ---
    parameters:
      - name: transaction_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Deleted
      404:
        description: No transaction with that id
    """
    if fetch_one(transaction_id) is None:
        return jsonify({"error": "not found"}), 404
    delete_transaction(transaction_id)
    return jsonify({"status": "deleted"})

@app.route('/api/summary', methods=['GET'])
@login_required
def api_summary():
    """Get income/expense totals
    ---
    responses:
      200:
        description: 'Totals grouped by t_type, e.g. Income 50000.0, Expense 2050.0'
    """
    return jsonify(get_summary())

@app.route('/api/inventory', methods=['GET'])
def api_list_inventory():
    """List all inventory stock levels
    ---
    responses:
      200:
        description: Every category/size combination with its current quantity
    """
    return jsonify([dict(row) for row in fetch_inventory()])

@app.route('/api/inventory/update', methods=['POST'])
@login_required
def api_update_inventory():
    """Set the stock quantity for one category/size
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [category, size, quantity]
          properties:
            category: {type: string, example: 'Half Pant'}
            size: {type: integer, example: 28}
            quantity: {type: integer, example: 40}
    responses:
      200:
        description: Updated
      400:
        description: Unknown category/size
    """
    data = request.get_json(force=True)
    category = data.get('category')
    size = data.get('size')
    if category not in CATEGORIES or size not in SIZES:
        return jsonify({"error": "unknown category or size"}), 400
    update_stock(category, size, int(data['quantity']))
    return jsonify({"status": "updated"})

if __name__ == '__main__':
    app.run(debug=True)
