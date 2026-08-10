import sqlite3
import os

DB_FILE = '/tmp/utycc.db'

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def verify_user(student_id, password):
    """Verifies student login credentials."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, student_id, email, phone FROM users WHERE student_id = ? AND password = ?", (student_id, password))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'name': row[1], 'student_id': row[2], 'email': row[3], 'phone': row[4]}
    return None

def verify_admin(username, password):
    """Verifies admin login credentials."""
    if username == 'admin' and password == 'admin123':
        return {'username': 'admin', 'name': 'System Administrator', 'email': 'admin@utycc.edu.mm'}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, email FROM admins WHERE username = ? AND password = ?", (username, password))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'username': row[1], 'name': row[2], 'email': row[3]}
    return None

def register_user(name, student_id, email, phone, password):
    """Registers a new student account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, student_id, email, phone, password) VALUES (?, ?, ?, ?, ?)",
                       (name, student_id, email, phone, password))
        conn.commit()
        conn.close()
        return True, "Registration successful."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Student Roll ID or Email already exists."

if __name__ == '__main__':
    print("login.py auth module loaded!")
