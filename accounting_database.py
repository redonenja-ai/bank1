import sqlite3
from collections import namedtuple
from datetime import date

# Database file
DB_FILE = "accounting.db"

# Named tuples
Transaction = namedtuple('Transaction', ['id', 'date', 'type', 'category', 'amount', 'description'])
Invoice = namedtuple('Invoice', ['id', 'invoice_number', 'client_name', 'amount', 'issue_date', 'due_date', 'description', 'paid', 'paid_date'])

# Categories
INCOME_CATEGORIES = ["Sales", "Services", "Interest", "Other Income"]
EXPENSE_CATEGORIES = ["Office Supplies", "Rent", "Utilities", "Marketing", "Travel", "Meals", "Equipment", "Software", "Taxes", "Other Expenses"]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT,
        type TEXT,
        category TEXT,
        amount REAL,
        description TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY,
        invoice_number TEXT UNIQUE,
        client_name TEXT,
        amount REAL,
        issue_date TEXT,
        due_date TEXT,
        description TEXT,
        paid INTEGER DEFAULT 0,
        paid_date TEXT
    )''')
    conn.commit()
    conn.close()

def add_transaction(date, type, category, amount, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO transactions (date, type, category, amount, description) VALUES (?, ?, ?, ?, ?)', 
              (date, type, category, amount, description))
    conn.commit()
    conn.close()

def get_transactions(type_=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if type_:
        c.execute('SELECT * FROM transactions WHERE type = ? ORDER BY date DESC', (type_,))
    else:
        c.execute('SELECT * FROM transactions ORDER BY date DESC')
    rows = c.fetchall()
    conn.close()
    return [Transaction(*row) for row in rows]

def add_invoice(invoice_num, client, amount, issue_date, due_date, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO invoices (invoice_number, client_name, amount, issue_date, due_date, description) VALUES (?, ?, ?, ?, ?, ?)', 
              (invoice_num, client, amount, issue_date, due_date, description))
    conn.commit()
    conn.close()

def get_invoices(paid=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if paid is None:
        c.execute('SELECT * FROM invoices ORDER BY issue_date DESC')
    elif paid:
        c.execute('SELECT * FROM invoices WHERE paid = 1 ORDER BY issue_date DESC')
    else:
        c.execute('SELECT * FROM invoices WHERE paid = 0 ORDER BY issue_date DESC')
    rows = c.fetchall()
    conn.close()
    return [Invoice(*row) for row in rows]

def mark_invoice_paid(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    paid_date = date.today().isoformat()
    c.execute('UPDATE invoices SET paid = 1, paid_date = ? WHERE id = ?', (paid_date, id))
    conn.commit()
    conn.close()

def delete_transaction(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM transactions WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def delete_invoice(id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM invoices WHERE id = ?', (id,))
    conn.commit()
    conn.close()

def get_dashboard_stats():
    transactions = get_transactions()
    total_revenue = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    profit = total_revenue - total_expenses
    
    # Monthly stats
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    month_revenue = sum(t.amount for t in transactions if t.type == 'income' and t.date.startswith(current_month))
    month_expenses = sum(t.amount for t in transactions if t.type == 'expense' and t.date.startswith(current_month))
    month_profit = month_revenue - month_expenses
    
    invoices = get_invoices(paid=False)
    outstanding_invoices = sum(inv.amount for inv in invoices)
    overdue_count = sum(1 for inv in invoices if inv.due_date < date.today().isoformat())
    
    return {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'profit': profit,
        'month_revenue': month_revenue,
        'month_expenses': month_expenses,
        'month_profit': month_profit,
        'outstanding_invoices': outstanding_invoices,
        'overdue_count': overdue_count
    }