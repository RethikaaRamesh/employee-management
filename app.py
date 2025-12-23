from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "infosys_secure_key"
DB_NAME = "database.db"

# ---------- DATABASE ----------
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            salary INTEGER
        )
    ''')

    # Create default admin if not exists
    cursor = conn.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if cursor.fetchone() is None:
        hashed = generate_password_hash("admin")
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", hashed)
        )

    conn.commit()
    return conn

# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = username
            flash("Login successful", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")

    return render_template('login.html')

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please login first", "error")
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')

    conn = get_db_connection()

    query = "SELECT * FROM employee WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    if role_filter:
        query += " AND role = ?"
        params.append(role_filter)

    employees = conn.execute(query, params).fetchall()
    roles = conn.execute("SELECT DISTINCT role FROM employee").fetchall()
    conn.close()

    return render_template(
        'dashboard.html',
        employees=employees,
        roles=roles,
        search=search,
        role_filter=role_filter
    )

# ---------- ADD EMPLOYEE ----------
@app.route('/add', methods=['POST'])
def add_employee():
    try:
        name = request.form['name']
        role = request.form['role']
        salary = request.form['salary']

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO employee (name, role, salary) VALUES (?, ?, ?)",
            (name, role, salary_toggle(salary))
        )
        conn.commit()
        conn.close()

        flash("Employee added successfully", "success")
    except:
        flash("Failed to add employee", "error")

    return redirect(url_for('dashboard'))

# ---------- UPDATE EMPLOYEE ----------
@app.route('/update/<int:id>', methods=['POST'])
def update_employee(id):
    try:
        role = request.form['role']
        salary = request.form['salary']

        conn = get_db_connection()
        conn.execute(
            "UPDATE employee SET role=?, salary=? WHERE id=?",
            (role, salary, id)
        )
        conn.commit()
        conn.close()

        flash("Employee updated successfully", "success")
    except:
        flash("Failed to update employee", "error")

    return redirect(url_for('dashboard'))

# ---------- DELETE EMPLOYEE ----------
@app.route('/delete/<int:id>')
def delete_employee(id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM employee WHERE id=?", (id,))
        conn.commit()
        conn.close()

        flash("Employee deleted successfully", "success")
    except:
        flash("Failed to delete employee", "error")

    return redirect(url_for('dashboard'))

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

# ---------- HELPER ----------
def salary_toggle(salary):
    try:
        return int(salary)
    except:
        return 0

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

