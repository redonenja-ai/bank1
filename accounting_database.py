import sqlite3
import datetime
from dataclasses import dataclass
from typing import List, Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "accounting.db")

@dataclass
class Transaction:
    id: int
    date: str
    type: str  # 'income' or 'expense'
    category: str
    amount: float
    description: str
    created_at: str

@dataclass
class Invoice:
    id: int
    invoice_number: str
    client_name: str
    amount: float
    issue_date: str
    due_date: str
    paid: bool
    paid_date: Optional[str]
    description: str
    created_at: str

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            amount REAL NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            paid INTEGER DEFAULT 0,
            paid_date TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Transaction functions
def add_transaction(date: str, type_: str, category: str, amount: float, description: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (date, type, category, amount, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, type_, category, amount, description))
    conn.commit()
    conn.close()

def get_transactions(type_: Optional[str] = None, start_date: Optional[str] = None, 
                     end_date: Optional[str] = None) -> List[Transaction]:
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if type_:
        query += " AND type = ?"
        params.append(type_)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [Transaction(*row) for row in rows]

def delete_transaction(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def update_transaction(id: int, date: str = None, category: str = None, amount: float = None, description: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if date is not None:
        updates.append("date = ?")
        params.append(date)
    if category is not None:
        updates.append("category = ?")
        params.append(category)
    if amount is not None:
        updates.append("amount = ?")
        params.append(amount)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if updates:
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?"
        params.append(id)
        cursor.execute(query, params)
        conn.commit()
    conn.close()

# Invoice functions
def add_invoice(invoice_number: str, client_name: str, amount: float, 
                issue_date: str, due_date: str, description: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (invoice_number, client_name, amount, issue_date, due_date, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (invoice_number, client_name, amount, issue_date, due_date, description))
    conn.commit()
    conn.close()

def get_invoices(paid: Optional[bool] = None) -> List[Invoice]:
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []
    
    if paid is not None:
        query += " AND paid = ?"
        params.append(1 if paid else 0)
    
    query += " ORDER BY issue_date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [Invoice(
        id=row[0],
        invoice_number=row[1],
        client_name=row[2],
        amount=row[3],
        issue_date=row[4],
        due_date=row[5],
        paid=bool(row[6]),
        paid_date=row[7],
        description=row[8],
        created_at=row[9]
    ) for row in rows]

def mark_invoice_paid(invoice_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.date.today().isoformat()
    cursor.execute('''
        UPDATE invoices SET paid = 1, paid_date = ? WHERE id = ?
    ''', (today, invoice_id))
    conn.commit()
    conn.close()

def delete_invoice(invoice_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()

def update_invoice(invoice_id: int, invoice_number: str = None, client_name: str = None, 
                   amount: float = None, issue_date: str = None, due_date: str = None, 
                   description: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if invoice_number is not None:
        updates.append("invoice_number = ?")
        params.append(invoice_number)
    if client_name is not None:
        updates.append("client_name = ?")
        params.append(client_name)
    if amount is not None:
        updates.append("amount = ?")
        params.append(amount)
    if issue_date is not None:
        updates.append("issue_date = ?")
        params.append(issue_date)
    if due_date is not None:
        updates.append("due_date = ?")
        params.append(due_date)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if updates:
        query = f"UPDATE invoices SET {', '.join(updates)} WHERE id = ?"
        params.append(invoice_id)
        cursor.execute(query, params)
        conn.commit()
    conn.close()

# Dashboard stats
def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    start_of_month = today.replace(day=1).isoformat()
    start_of_year = today.replace(month=1, day=1).isoformat()
    
    # Total revenue (income)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income'")
    total_revenue = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income' AND date >= ?", (start_of_month,))
    month_revenue = cursor.fetchone()[0]
    
    # Total expenses
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense'")
    total_expenses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense' AND date >= ?", (start_of_month,))
    month_expenses = cursor.fetchone()[0]
    
    # Outstanding invoices
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE paid = 0")
    outstanding = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE paid = 0 AND due_date < ?", (today.isoformat(),))
    overdue_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'total_expenses': total_expenses,
        'month_expenses': month_expenses,
        'profit': total_revenue - total_expenses,
        'month_profit': month_revenue - month_expenses,
        'outstanding_invoices': outstanding,
        'overdue_count': overdue_count
    }

# Categories
INCOME_CATEGORIES = [
    "Sales", "Services", "Consulting", "Product Sales", 
    "Subscriptions", "Licensing", "Other Income"
]

EXPENSE_CATEGORIES = [
    "Office Supplies", "Rent", "Utilities", "Salaries", 
    "Marketing", "Software", "Travel", "Meals", 
    "Equipment", "Insurance", "Taxes", "Professional Services",
    "Other Expense"
]