import json
import os
import re
import shutil
import smtplib
import sqlite3
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "utycc.db")

# Gmail Configurations
GMAIL_SENDER = "sithukyaw6mdy@gmail.com"
GMAIL_APP_PASSWORD = "mmvxpntlwlhezwml"


def get_db_connection():
    try:
        conn = sqlite3.connect(DB_FILE, timeout=30)
        return conn
    except Exception:
        try:
            tmp_path = os.path.join(os.path.dirname(DB_FILE), ".tmp_utycc.db")
            if os.path.exists(DB_FILE) and not os.path.exists(tmp_path):
                shutil.copy2(DB_FILE, tmp_path)
            conn = sqlite3.connect(tmp_path, timeout=30)
            return conn
        except Exception:
            return sqlite3.connect(DB_FILE, timeout=30)


def init_sqlite_db():
    db_dir = os.path.dirname(DB_FILE)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        student_id TEXT NOT NULL UNIQUE,
        email TEXT UNIQUE,
        phone TEXT,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'student',
        avatar TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in cursor.fetchall()]
    if "avatar" not in user_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
        except Exception:
            pass
    if "phone" not in user_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        except Exception:
            pass
    if "role" not in user_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
        except Exception:
            pass

    # Admins Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        name TEXT,
        email TEXT,
        role TEXT DEFAULT 'super_admin',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")
    cursor.execute("PRAGMA table_info(admins)")
    admin_cols = [col[1] for col in cursor.fetchall()]
    if "role" not in admin_cols:
        try:
            cursor.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'super_admin'")
        except Exception:
            pass

    # Hostels Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS hostels (
        hostel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_name TEXT NOT NULL,
        room_number TEXT NOT NULL,
        gender_type TEXT DEFAULT 'Boys',
        capacity INTEGER DEFAULT 4,
        available_beds INTEGER DEFAULT 4,
        description TEXT,
        image_url TEXT,
        kpay_qr_url TEXT,
        status TEXT DEFAULT 'Active',
        admin_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")
    cursor.execute("PRAGMA table_info(hostels)")
    hostel_cols = [col[1] for col in cursor.fetchall()]
    if "admin_id" not in hostel_cols:
        try:
            cursor.execute("ALTER TABLE hostels ADD COLUMN admin_id INTEGER")
        except Exception:
            pass
    if "kpay_qr_url" not in hostel_cols:
        try:
            cursor.execute("ALTER TABLE hostels ADD COLUMN kpay_qr_url TEXT")
        except Exception:
            pass
    if "status" not in hostel_cols:
        try:
            cursor.execute("ALTER TABLE hostels ADD COLUMN status TEXT DEFAULT 'Active'")
        except Exception:
            pass

    # Hostel Bookings Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS hostel_bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        student_year TEXT NOT NULL,
        student_id TEXT NOT NULL,
        national_id TEXT NOT NULL,
        payment_method TEXT DEFAULT 'KBZPay (KPay QR)',
        transaction_id TEXT,
        amount TEXT DEFAULT 'Ks',
        payment_status TEXT DEFAULT 'Pending',
        booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Pending Approval',
        FOREIGN KEY (hostel_id) REFERENCES hostels(hostel_id)
    );""")

    # Ferry Groups Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS ferry_groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT NOT NULL,
        description TEXT,
        admin_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES admins(id)
    );""")
    cursor.execute("PRAGMA table_info(ferry_groups)")
    fg_cols = [col[1] for col in cursor.fetchall()]
    if "admin_id" not in fg_cols:
        try:
            cursor.execute("ALTER TABLE ferry_groups ADD COLUMN admin_id INTEGER")
        except Exception:
            pass

    # Ferries Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS ferries (
        ferry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        ferry_name TEXT NOT NULL,
        route_name TEXT,
        departure_time TEXT,
        capacity INTEGER DEFAULT 40,
        available_seats INTEGER DEFAULT 40,
        kpay_qr_url TEXT,
        status TEXT DEFAULT 'Active',
        admin_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES ferry_groups(group_id)
    );""")
    cursor.execute("PRAGMA table_info(ferries)")
    ferry_cols = [col[1] for col in cursor.fetchall()]
    if "admin_id" not in ferry_cols:
        try:
            cursor.execute("ALTER TABLE ferries ADD COLUMN admin_id INTEGER")
        except Exception:
            pass
    if "kpay_qr_url" not in ferry_cols:
        try:
            cursor.execute("ALTER TABLE ferries ADD COLUMN kpay_qr_url TEXT")
        except Exception:
            pass
    if "status" not in ferry_cols:
        try:
            cursor.execute("ALTER TABLE ferries ADD COLUMN status TEXT DEFAULT 'Active'")
        except Exception:
            pass

    # Ferry Bookings Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS ferry_bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ferry_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        student_year TEXT NOT NULL,
        student_id TEXT NOT NULL,
        student_phone TEXT NOT NULL,
        payment_method TEXT DEFAULT 'KBZPay (KPay QR)',
        transaction_id TEXT,
        amount TEXT DEFAULT 'Ks',
        payment_status TEXT DEFAULT 'Pending',
        booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Pending Approval',
        FOREIGN KEY (ferry_id) REFERENCES ferries(ferry_id)
    );""")

    # Reviews Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        rating INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")

    # Inquiries Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS inquiries (
        inquiry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        student_id TEXT NOT NULL,
        email TEXT,
        service_category TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")
    cursor.execute("PRAGMA table_info(inquiries)")
    inq_cols = [col[1] for col in cursor.fetchall()]
    if "email" not in inq_cols:
        try:
            cursor.execute("ALTER TABLE inquiries ADD COLUMN email TEXT")
        except Exception:
            pass

    # Default Super Admin Seed
    cursor.execute("SELECT id FROM admins WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO admins (username, password, name, email, role) VALUES (?, ?, ?, ?, ?)",
            ("admin", "admin123", "System Administrator (Super)", "admin@utycc.edu.mm", "super_admin")
        )
    conn.commit()
    conn.close()


def is_super_admin(admin_id):
    if not admin_id:
        return True
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM admins WHERE id = ?", (admin_id,))
        row = cursor.fetchone()
        conn.close()
        if row and (row[0] or "").strip().lower() == "super_admin":
            return True
    except Exception:
        pass
    return False


def verify_user(student_id, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, student_id, email, phone, role, avatar FROM users WHERE TRIM(student_id)=? AND password=?",
        (str(student_id).strip(), str(password))
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        u_id, u_name, u_s_id, u_email, u_phone, u_role, u_avatar = row
        return {
            "id": u_id,
            "name": u_name,
            "student_id": u_s_id,
            "email": u_email,
            "phone": u_phone,
            "role": u_role,
            "avatar": u_avatar or "",
            "profile_pic": u_avatar or "",
        }
    return None


def register_user(name, student_id, email, phone, password):
    email_regex = r'^[a-zA-Z0-9_.+-]+@gmail\.com$'
    if not re.match(email_regex, str(email).strip()):
        return False, "ကျေးဇူးပြု၍ မှန်ကန်သော Gmail လိပ်စာ (@gmail.com) ကိုသာ ထည့်သွင်းပါ။"
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_student_id = str(student_id).strip()
    cursor.execute("SELECT id FROM users WHERE TRIM(student_id)=?", (clean_student_id,))
    if cursor.fetchone():
        conn.close()
        return False, "Student ID already registered."
    cursor.execute(
        "INSERT INTO users (name, student_id, email, phone, password) VALUES (?, ?, ?, ?, ?)",
        (str(name).strip(), clean_student_id, str(email).strip(), str(phone).strip(), str(password))
    )
    conn.commit()
    conn.close()
    return True, "Registration successful."


def verify_admin(username, password, role=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, name, email, role FROM admins WHERE username=? AND password=?",
        (username, password)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        a_id, a_username, a_name, a_email, a_role = row
        db_role = (a_role or "super_admin").lower()
        if role and str(role).strip():
            req_role = str(role).strip().lower()
            if req_role == "super_admin" and db_role != "super_admin":
                return None
            if req_role in ["hostel", "ferry"] and db_role != req_role and db_role != "super_admin":
                return None
        return {
            "id": a_id,
            "username": a_username,
            "name": a_name,
            "email": a_email,
            "role": db_role,
        }
    return None


def send_verification_email(receiver_email, otp_code):
    message = MIMEMultipart("alternative")
    message["Subject"] = "UTYCC Portal - Email Verification OTP"
    message["From"] = GMAIL_SENDER
    message["To"] = receiver_email
    text = f"Your UTYCC Portal verification code is: {otp_code}"
    html = f"<p>Your UTYCC Portal verification code is: <b>{otp_code}</b></p>"
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def send_gmail_notification(to_email, full_name, student_id, service_category, message_body):
    subject = f"[UTYCC Portal] New Inquiry: {service_category} from {full_name}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f6f9; border-radius: 10px;">
        <h2 style="color: #0284c7;">UTYCC Smart Campus - New Inquiry Received</h2>
        <p><b>Full Name:</b> {full_name}</p>
        <p><b>Student ID / Roll No:</b> {student_id}</p>
        <p><b>Service Category:</b> {service_category}</p>
        <p><b>Message Details:</b></p>
        <div style="background: #ffffff; padding: 15px; border-left: 4px solid #0284c7; border-radius: 5px;">
            {message_body}
        </div>
        <p style="font-size: 12px; color: #666; margin-top: 20px;">This is an automated notification from UTYCC Enterprise Portal.</p>
    </div>
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = to_email
    msg.attach(MIMEText(html_content, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, to_email, msg.as_string())
        return True
    except Exception as e:
        print("Gmail Error:", e)
        return False


class UTYCCPortalHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            query_params = urllib.parse.parse_qs(parsed.query)

            if path in ["/", "/index.html", "/home", "/home.html"]:
                self.serve_file("home.html")
                return
            elif path in ["/ferry", "/ferry.html"]:
                self.serve_file("ferry.html")
                return
            elif path in ["/hostel", "/hostel.html"]:
                self.serve_file("hostel.html")
                return
            elif path in ["/login", "/login.html"]:
                self.serve_file("login.html")
                return
            elif path in ["/admin-login", "/admin-login.html", "/templates/admin-login.html"]:
                self.serve_file("admin-login.html")
                return
            elif path in ["/admin", "/admin.html", "/templates/admin.html"]:
                self.serve_file("admin.html")
                return
            elif path in ["/profile", "/profile.html", "/templates/profile.html"]:
                self.serve_file("profile.html")
                return
            elif path == "/api/admin/overview" or path.startswith("/api/admin/overview"):
                role = query_params.get("role", [""])[0]
                admin_id = query_params.get("admin_id", [None])[0]
                self.handle_admin_overview(role=role, admin_id=admin_id)
                return
            elif path in ["/api/ferries", "/api/ferry/list", "/api/ferry"]:
                self.handle_get_ferries()
                return
            elif path in ["/api/ferry_groups", "/api/ferry-groups", "/api/ferry/groups", "/api/ferry_group"]:
                self.handle_get_ferry_groups()
                return
            elif path.startswith("/api/ferries-by-group/"):
                group_id = path.split("/")[-1]
                self.handle_get_ferries_by_group(group_id)
                return
            elif path in ["/api/hostels", "/api/hostel/list", "/api/hostel"]:
                self.handle_get_hostels()
                return
            elif path.startswith("/api/user-status/"):
                student_id = urllib.parse.unquote(path.split("/")[-1])
                self.handle_user_status(student_id)
                return
            elif path == "/api/reviews":
                self.handle_get_reviews()
                return
            return super().do_GET()
        except Exception as e:
            print(f"do_GET error: {e}")
            self.send_json({"success": False, "message": str(e)}, 500)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            data = {}
            try:
                data = json.loads(post_data.decode("utf-8"))
            except Exception:
                pass

            path = self.path
            if path in ["/api/user/update-profile", "/api/update-profile", "/api/update-profile-pic"]:
                self.handle_update_profile(data)
            elif path in ["/api/user/change-password", "/api/change-password"]:
                self.handle_change_password(data)
            elif path == "/api/login":
                self.handle_user_login(data)
            elif path == "/api/register":
                self.handle_user_register(data)
            elif path == "/api/admin/login":
                self.handle_admin_login(data)
            elif path == "/api/admin/register":
                self.handle_admin_register(data)
            elif path == "/api/admin/create-admin":
                self.handle_create_admin(data)
            elif path == "/api/admin/delete-admin":
                self.handle_delete_admin(data)
            elif path in ["/api/admin/delete-student", "/api/delete-student"]:
                self.handle_delete_student(data)
            elif path in ["/api/admin/delete-all-students", "/api/delete-all-students"]:
                self.handle_delete_all_students(data)
            elif path == "/api/admin/add-hostel":
                self.handle_add_hostel(data)
            elif path in ["/api/admin/edit-hostel", "/api/admin/update-hostel"]:
                self.handle_edit_hostel(data)
            elif path == "/api/admin/toggle-hostel-status":
                self.handle_toggle_hostel_status(data)
            elif path == "/api/admin/delete-hostel":
                self.handle_delete_hostel(data)
            elif path == "/api/admin/add-ferry-group":
                self.handle_add_ferry_group(data)
            elif path == "/api/admin/delete-ferry-group":
                self.handle_delete_ferry_group(data)
            elif path == "/api/admin/add-ferry":
                self.handle_add_ferry(data)
            elif path in ["/api/admin/edit-ferry", "/api/admin/update-ferry"]:
                self.handle_edit_ferry(data)
            elif path == "/api/admin/toggle-ferry-status":
                self.handle_toggle_ferry_status(data)
            elif path == "/api/admin/delete-ferry":
                self.handle_delete_ferry(data)
            elif path in ["/api/hostel/book", "/api/book-hostel"]:
                self.handle_hostel_book(data)
            elif path in ["/api/ferry/book", "/api/book-ferry"]:
                self.handle_ferry_book(data)
            elif path == "/api/inquiry":
                self.handle_inquiry(data)
            elif path == "/api/cancel-hostel":
                self.handle_cancel_hostel(data)
            elif path == "/api/cancel-ferry":
                self.handle_cancel_ferry(data)
            elif path in ["/api/hostel/update-booking", "/api/update-hostel-booking"]:
                self.handle_hostel_update_booking(data)
            elif path in ["/api/ferry/update-booking", "/api/update-ferry-booking"]:
                self.handle_ferry_update_booking(data)
            elif path == "/api/reviews":
                self.handle_add_review(data)
            elif path == "/api/admin/confirm-payment":
                self.handle_admin_confirm_payment(data)
            else:
                self.send_json({"success": False, "message": "Route not found"}, 404)
        except Exception as e:
            print(f"do_POST error: {e}")
            self.send_json({"success": False, "message": str(e)}, 500)

    def serve_file(self, filename):
        target = os.path.join(BASE_DIR, filename)
        if not os.path.exists(target):
            target = os.path.join(BASE_DIR, "templates", filename)
        if os.path.exists(target):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.end_headers()
            with open(target, "rb") as f:
                self.wfile.write(f.read())

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def handle_update_profile(self, data):
        user_id = data.get("id") or data.get("user_id")
        old_student_id = str(data.get("old_student_id", "") or data.get("current_student_id", "")).strip()
        student_id = str(data.get("student_id", "") or data.get("new_student_id", "")).strip()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        phone = str(data.get("phone", "")).strip()
        avatar = str(data.get("avatar", "") or data.get("profile_pic", "")).strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        row = None
        # 1. Look up by user DB id if provided
        if user_id:
            cursor.execute("SELECT id, name, student_id, email, phone, avatar FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

        # 2. Look up by old_student_id if explicitly passed
        if not row and old_student_id:
            cursor.execute("SELECT id, name, student_id, email, phone, avatar FROM users WHERE TRIM(student_id) = ?", (old_student_id,))
            row = cursor.fetchone()

        # 3. Look up by student_id
        if not row and student_id:
            cursor.execute("SELECT id, name, student_id, email, phone, avatar FROM users WHERE TRIM(student_id) = ?", (student_id,))
            row = cursor.fetchone()

        # 4. Fallback search by email if student_id was updated
        if not row and email:
            cursor.execute("SELECT id, name, student_id, email, phone, avatar FROM users WHERE TRIM(email) = ?", (email,))
            row = cursor.fetchone()

        if not row:
            conn.close()
            self.send_json({"success": False, "message": "User not found."}, 404)
            return

        u_id, ex_name, ex_student_id, ex_email, ex_phone, ex_avatar = row

        final_student_id = student_id if student_id else ex_student_id
        final_name = name if name else ex_name
        final_email = email if email else ex_email
        final_phone = phone if phone else ex_phone
        final_avatar = avatar if avatar else ex_avatar

        # Check if the new student_id belongs to another registered account
        if final_student_id != ex_student_id:
            cursor.execute("SELECT id FROM users WHERE TRIM(student_id) = ? AND id != ?", (final_student_id, u_id))
            if cursor.fetchone():
                conn.close()
                self.send_json({"success": False, "message": "Student Roll ID is already taken by another account."}, 400)
                return

        # Update users table
        cursor.execute(
            "UPDATE users SET student_id=?, name=?, email=?, phone=?, avatar=? WHERE id=?",
            (final_student_id, final_name, final_email, final_phone, final_avatar, u_id)
        )

        # Update existing bookings and inquiries if student_id changed
        if final_student_id != ex_student_id:
            cursor.execute("UPDATE hostel_bookings SET student_id=? WHERE TRIM(student_id)=?", (final_student_id, ex_student_id))
            cursor.execute("UPDATE ferry_bookings SET student_id=? WHERE TRIM(student_id)=?", (final_student_id, ex_student_id))
            cursor.execute("UPDATE inquiries SET student_id=? WHERE TRIM(student_id)=?", (final_student_id, ex_student_id))

        conn.commit()
        conn.close()

        self.send_json({
            "success": True,
            "message": "Profile updated successfully!",
            "user": {
                "id": u_id,
                "student_id": final_student_id,
                "name": final_name,
                "email": final_email,
                "phone": final_phone,
                "avatar": final_avatar,
                "profile_pic": final_avatar
            }
        })

    def handle_change_password(self, data):
        user_id = data.get("id") or data.get("user_id")
        student_id = str(data.get("student_id", "")).strip()
        current_password = str(data.get("current_password", "")).strip()
        new_password = str(data.get("new_password", "")).strip()

        if not current_password or not new_password:
            self.send_json({"success": False, "message": "Current password and new password are required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        user_row = None
        if user_id:
            cursor.execute("SELECT id FROM users WHERE id = ? AND password = ?", (user_id, current_password))
            user_row = cursor.fetchone()
        if not user_row and student_id:
            cursor.execute("SELECT id FROM users WHERE TRIM(student_id) = ? AND password = ?", (student_id, current_password))
            user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            self.send_json({"success": False, "message": "လက်ရှိ စကားဝှက် မှားယွင်းနေပါသည်။"}, 400)
            return

        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_row[0]))
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "စကားဝှက် အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။"})

    def handle_admin_register(self, data):
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", "")).strip()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        role = str(data.get("role", "hostel")).strip().lower()

        if role == "super_admin":
            self.send_json({"success": False, "message": "Public registration for Super Admin role is restricted."}, 403)
            return

        if not username or not password:
            self.send_json({"success": False, "message": "Username and password are required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM admins WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            self.send_json({"success": False, "message": "Admin username already registered."}, 400)
            return

        cursor.execute(
            "INSERT INTO admins (username, password, name, email, role) VALUES (?, ?, ?, ?, ?)",
            (username, password, name or username, email or f"{username}@utycc.edu.mm", role)
        )
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": f"{role.upper()} Admin account registered successfully!"})

    def handle_create_admin(self, data):
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", "")).strip()
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip()
        role = str(data.get("role", "hostel")).strip().lower()

        if not username or not password:
            self.send_json({"success": False, "message": "Username and Password are required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM admins WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            self.send_json({"success": False, "message": "Username already exists."}, 400)
            return

        cursor.execute(
            "INSERT INTO admins (username, password, name, email, role) VALUES (?, ?, ?, ?, ?)",
            (username, password, name or username, email or f"{username}@utycc.edu.mm", role)
        )
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": f"New {role.upper()} account created successfully!"})

    def handle_delete_student(self, data):
        admin_id = data.get("admin_id")
        if not is_super_admin(admin_id):
            self.send_json({"success": False, "message": "Unauthorized. Only Super Admin can delete student accounts."}, 403)
            return

        student_id = data.get("student_id") or data.get("id") or data.get("target_student_id")
        if not student_id:
            self.send_json({"success": False, "message": "Student ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ? OR TRIM(student_id) = ?", (student_id, str(student_id).strip()))
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Student account deleted successfully!"})

    def handle_delete_all_students(self, data):
        admin_id = data.get("admin_id")
        if not is_super_admin(admin_id):
            self.send_json({"success": False, "message": "Unauthorized. Only Super Admin can delete student accounts."}, 403)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE role = 'student' OR role IS NULL OR role = ''")
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "All registered student accounts deleted successfully!"})

    def handle_delete_admin(self, data):
        admin_id = data.get("admin_id")
        target_admin_id = data.get("target_admin_id") or data.get("id")

        if not is_super_admin(admin_id):
            self.send_json({"success": False, "message": "Unauthorized. Only Super Admin can delete admin accounts."}, 403)
            return

        if not target_admin_id:
            self.send_json({"success": False, "message": "Admin ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM admins WHERE id = ?", (target_admin_id,))
        row = cursor.fetchone()
        if row and row[0] == "admin":
            conn.close()
            self.send_json({"success": False, "message": "System Administrator (admin) account cannot be deleted."}, 400)
            return

        cursor.execute("DELETE FROM admins WHERE id = ?", (target_admin_id,))
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Admin account deleted successfully!"})

    def handle_add_hostel(self, data):
        admin_id = data.get("admin_id")
        hostel_name = str(data.get("hostel_name", "")).strip()
        room_number = str(data.get("room_number", "")).strip()
        gender_type = str(data.get("gender_type", "Boys")).strip()
        capacity = int(data.get("capacity", 4))
        available_beds = int(data.get("available_beds", capacity))
        description = str(data.get("description", "")).strip()
        image_url = str(data.get("image_url", "")).strip() or ""
        kpay_qr_url = str(data.get("kpay_qr_url", "")).strip() or ""

        if not hostel_name or not room_number:
            self.send_json({"success": False, "message": "Hostel Name and Room Number are required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO hostels (hostel_name, room_number, gender_type, capacity, available_beds, description, image_url, kpay_qr_url, admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (hostel_name, room_number, gender_type, capacity, available_beds, description, image_url, kpay_qr_url, admin_id)
        )
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Hostel block added successfully!"})

    def handle_edit_hostel(self, data):
        hostel_id = data.get("hostel_id") or data.get("id")
        admin_id = data.get("admin_id")
        hostel_name = str(data.get("hostel_name", "")).strip()
        room_number = str(data.get("room_number", "")).strip()
        gender_type = str(data.get("gender_type", "Boys")).strip()
        capacity = int(data.get("capacity", 4))
        available_beds = int(data.get("available_beds", capacity))
        description = str(data.get("description", "")).strip()
        image_url = str(data.get("image_url", "")).strip()
        kpay_qr_url = str(data.get("kpay_qr_url", "")).strip() or ""
        status = str(data.get("status", "Active")).strip()

        if not hostel_id or not hostel_name or not room_number:
            self.send_json({"success": False, "message": "Hostel ID, Name, and Room Number are required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        if is_super_admin(admin_id):
            cursor.execute(
                """UPDATE hostels SET hostel_name=?, room_number=?, gender_type=?, capacity=?, available_beds=?, description=?, image_url=?, kpay_qr_url=?, status=? WHERE hostel_id=?""",
                (hostel_name, room_number, gender_type, capacity, available_beds, description, image_url, kpay_qr_url, status, hostel_id)
            )
        else:
            cursor.execute(
                """UPDATE hostels SET hostel_name=?, room_number=?, gender_type=?, capacity=?, available_beds=?, description=?, image_url=?, kpay_qr_url=?, status=? WHERE hostel_id=? AND (admin_id=? OR admin_id IS NULL)""",
                (hostel_name, room_number, gender_type, capacity, available_beds, description, image_url, kpay_qr_url, status, hostel_id, admin_id)
            )
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Hostel information updated successfully!"})

    def handle_toggle_hostel_status(self, data):
        hostel_id = data.get("hostel_id") or data.get("id")
        admin_id = data.get("admin_id")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM hostels WHERE hostel_id = ?", (hostel_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            self.send_json({"success": False, "message": "Hostel not found"}, 404)
            return

        current_status = row[0] or "Active"
        new_status = "Inactive" if current_status == "Active" else "Active"

        if is_super_admin(admin_id):
            cursor.execute("UPDATE hostels SET status = ? WHERE hostel_id = ?", (new_status, hostel_id))
        else:
            cursor.execute("UPDATE hostels SET status = ? WHERE hostel_id = ? AND (admin_id = ? OR admin_id IS NULL)", (new_status, hostel_id, admin_id))

        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": f"Hostel status set to {new_status}", "status": new_status})

    def handle_delete_hostel(self, data):
        hostel_id = data.get("hostel_id")
        admin_id = data.get("admin_id")

        conn = get_db_connection()
        cursor = conn.cursor()
        if is_super_admin(admin_id):
            cursor.execute("DELETE FROM hostels WHERE hostel_id = ?", (hostel_id,))
        else:
            cursor.execute("DELETE FROM hostels WHERE hostel_id = ? AND (admin_id = ? OR admin_id IS NULL)", (hostel_id, admin_id))
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Hostel block removed successfully!"})

    def handle_add_ferry_group(self, data):
        admin_id = data.get("admin_id")
        group_name = str(data.get("group_name", "")).strip()
        description = str(data.get("description", "")).strip()

        if not group_name:
            self.send_json({"success": False, "message": "Group Name is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ferry_groups (group_name, description, admin_id) VALUES (?, ?, ?)",
            (group_name, description, admin_id)
        )
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Ferry route group created successfully!"})

    def handle_delete_ferry_group(self, data):
        group_id = data.get("group_id")
        admin_id = data.get("admin_id")

        conn = get_db_connection()
        cursor = conn.cursor()
        if is_super_admin(admin_id):
            cursor.execute("DELETE FROM ferry_groups WHERE group_id = ?", (group_id,))
        else:
            cursor.execute("DELETE FROM ferry_groups WHERE group_id = ? AND (admin_id = ? OR admin_id IS NULL)", (group_id, admin_id))
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Ferry group removed successfully!"})

    def handle_add_ferry(self, data):
        admin_id = data.get("admin_id")
        ferry_name = str(data.get("ferry_name", "")).strip()
        route_name = str(data.get("route_name", "")).strip()
        departure_time = str(data.get("departure_time", "07:00 AM")).strip()
        capacity = int(data.get("capacity", 40))
        available_seats = int(data.get("available_seats", capacity))
        group_id = int(data.get("group_id", 1))
        kpay_qr_url = str(data.get("kpay_qr_url", "")).strip() or ""

        if not ferry_name or not route_name:
            self.send_json({"success": False, "message": "Ferry Name and Route Name are required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO ferries (group_id, ferry_name, route_name, departure_time, capacity, available_seats, kpay_qr_url, admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (group_id, ferry_name, route_name, departure_time, capacity, available_seats, kpay_qr_url, admin_id)
        )
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Ferry line added successfully!"})

    def handle_edit_ferry(self, data):
        ferry_id = data.get("ferry_id") or data.get("id")
        admin_id = data.get("admin_id")
        group_id = int(data.get("group_id", 1))
        ferry_name = str(data.get("ferry_name", "")).strip()
        route_name = str(data.get("route_name", "")).strip()
        departure_time = str(data.get("departure_time", "07:00 AM")).strip()
        capacity = int(data.get("capacity", 40))
        available_seats = int(data.get("available_seats", capacity))
        kpay_qr_url = str(data.get("kpay_qr_url", "")).strip() or ""
        status = str(data.get("status", "Active")).strip()

        if not ferry_id or not ferry_name or not route_name:
            self.send_json({"success": False, "message": "Ferry ID, Name, and Route Name are required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        if is_super_admin(admin_id):
            cursor.execute(
                """UPDATE ferries SET group_id=?, ferry_name=?, route_name=?, departure_time=?, capacity=?, available_seats=?, kpay_qr_url=?, status=? WHERE ferry_id=?""",
                (group_id, ferry_name, route_name, departure_time, capacity, available_seats, kpay_qr_url, status, ferry_id)
            )
        else:
            cursor.execute(
                """UPDATE ferries SET group_id=?, ferry_name=?, route_name=?, departure_time=?, capacity=?, available_seats=?, kpay_qr_url=?, status=? WHERE ferry_id=? AND (admin_id=? OR admin_id IS NULL)""",
                (group_id, ferry_name, route_name, departure_time, capacity, available_seats, kpay_qr_url, status, ferry_id, admin_id)
            )
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Ferry route updated successfully!"})

    def handle_toggle_ferry_status(self, data):
        ferry_id = data.get("ferry_id") or data.get("id")
        admin_id = data.get("admin_id")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM ferries WHERE ferry_id = ?", (ferry_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            self.send_json({"success": False, "message": "Ferry line not found"}, 404)
            return

        current_status = row[0] or "Active"
        new_status = "Inactive" if current_status == "Active" else "Active"

        if is_super_admin(admin_id):
            cursor.execute("UPDATE ferries SET status = ? WHERE ferry_id = ?", (new_status, ferry_id))
        else:
            cursor.execute("UPDATE ferries SET status = ? WHERE ferry_id = ? AND (admin_id = ? OR admin_id IS NULL)", (new_status, ferry_id, admin_id))

        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": f"Ferry status set to {new_status}", "status": new_status})

    def handle_delete_ferry(self, data):
        ferry_id = data.get("ferry_id")
        admin_id = data.get("admin_id")

        conn = get_db_connection()
        cursor = conn.cursor()
        if is_super_admin(admin_id):
            cursor.execute("DELETE FROM ferries WHERE ferry_id = ?", (ferry_id,))
        else:
            cursor.execute("DELETE FROM ferries WHERE ferry_id = ? AND (admin_id = ? OR admin_id IS NULL)", (ferry_id, admin_id))
        conn.commit()
        conn.close()

        self.send_json({"success": True, "message": "Ferry line removed successfully!"})

    def handle_get_ferries(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ferry_id, group_id, ferry_name, route_name, departure_time, capacity, available_seats, status, kpay_qr_url FROM ferries"
        )
        rows = cursor.fetchall()
        conn.close()

        ferries = []
        for fid, gid, fname, rname, dtime, cap, aseats, st, kpay in rows:
            ferries.append({
                "ferry_id": fid,
                "group_id": gid,
                "ferry_name": fname,
                "route_name": rname,
                "departure_time": dtime,
                "capacity": cap,
                "available_seats": aseats,
                "status": st,
                "kpay_qr_url": kpay or "",
            })
        self.send_json({"success": True, "ferries": ferries, "data": ferries})

    def handle_get_ferry_groups(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT group_id, group_name, description FROM ferry_groups")
        rows = cursor.fetchall()
        conn.close()

        groups = []
        for gid, gname, desc in rows:
            groups.append({"group_id": gid, "group_name": gname, "description": desc})
        self.send_json({"success": True, "groups": groups, "data": groups})

    def handle_get_ferries_by_group(self, group_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ferry_id, group_id, ferry_name, route_name, departure_time, capacity, available_seats, status, kpay_qr_url FROM ferries WHERE group_id = ?",
            (group_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        ferries = []
        for fid, gid, fname, rname, dtime, cap, aseats, st, kpay in rows:
            ferries.append({
                "ferry_id": fid,
                "group_id": gid,
                "ferry_name": fname,
                "route_name": rname,
                "departure_time": dtime,
                "capacity": cap,
                "available_seats": aseats,
                "status": st,
                "kpay_qr_url": kpay or "",
            })
        self.send_json({"success": True, "ferries": ferries})

    def handle_get_hostels(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT hostel_id, hostel_name, room_number, gender_type, capacity, available_beds, description, image_url, status, kpay_qr_url FROM hostels"
        )
        rows = cursor.fetchall()
        conn.close()

        hostels = []
        for hid, hname, rnum, gtype, cap, abeds, desc, img, st, kpay in rows:
            hostels.append({
                "hostel_id": hid,
                "hostel_name": hname,
                "room_number": rnum,
                "gender_type": gtype,
                "capacity": cap,
                "available_beds": abeds,
                "description": desc,
                "image_url": img,
                "status": st,
                "kpay_qr_url": kpay or "",
            })
        self.send_json({"success": True, "hostels": hostels, "data": hostels})

    def handle_user_status(self, student_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        clean_sid = str(student_id).strip()

        cursor.execute("SELECT id, name, student_id, email, phone, role, avatar FROM users WHERE TRIM(student_id) = ?", (clean_sid,))
        user_row = cursor.fetchone()
        user_data = None
        if user_row:
            u_id, u_name, u_sid, u_email, u_phone, u_role, u_avatar = user_row
            user_data = {
                "id": u_id,
                "name": u_name,
                "student_id": u_sid,
                "email": u_email or "",
                "phone": u_phone or "",
                "role": u_role or "student",
                "avatar": u_avatar or "",
                "profile_pic": u_avatar or ""
            }

        cursor.execute(
            "SELECT hb.booking_id, h.hostel_id, h.hostel_name, h.room_number, hb.payment_status, hb.status, hb.student_name, hb.student_year, hb.national_id, hb.transaction_id FROM hostel_bookings hb JOIN hostels h ON hb.hostel_id = h.hostel_id WHERE TRIM(hb.student_id) = ? AND hb.status != 'Cancelled' ORDER BY hb.booking_id DESC LIMIT 1",
            (clean_sid,)
        )
        hostel_row = cursor.fetchone()

        cursor.execute(
            "SELECT fb.booking_id, f.ferry_id, f.ferry_name, f.route_name, fb.payment_status, fb.status, fb.student_name, fb.student_year, fb.student_phone, fb.transaction_id FROM ferry_bookings fb JOIN ferries f ON fb.ferry_id = f.ferry_id WHERE TRIM(fb.student_id) = ? AND fb.status != 'Cancelled' ORDER BY fb.booking_id DESC LIMIT 1",
            (clean_sid,)
        )
        ferry_row = cursor.fetchone()
        conn.close()

        has_hostel = bool(hostel_row)
        hostel_data = None
        if hostel_row:
            h_bid, h_hid, h_hname, h_rnum, h_payst, h_st, h_sname, h_syear, h_nid, h_txid = hostel_row
            hostel_data = {
                "booking_id": h_bid,
                "hostel_id": h_hid,
                "hostel_name": h_hname,
                "room_number": h_rnum,
                "payment_status": h_payst,
                "status": h_st,
                "student_name": h_sname,
                "student_year": h_syear,
                "national_id": h_nid,
                "transaction_id": h_txid or "",
            }

        has_ferry = bool(ferry_row)
        ferry_data = None
        if ferry_row:
            f_bid, f_fid, f_fname, f_rname, f_payst, f_st, f_sname, f_syear, f_sphone, f_txid = ferry_row
            ferry_data = {
                "booking_id": f_bid,
                "ferry_id": f_fid,
                "ferry_name": f_fname,
                "route_name": f_rname,
                "payment_status": f_payst,
                "status": f_st,
                "student_name": f_sname,
                "student_year": f_syear,
                "student_phone": f_sphone,
                "transaction_id": f_txid or "",
            }

        self.send_json({
            "success": True,
            "user": user_data,
            "has_hostel": has_hostel,
            "hostel": hostel_data,
            "has_ferry": has_ferry,
            "ferry": ferry_data,
        })

    def handle_get_reviews(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT review_id, name, email, rating, review_text, created_at FROM reviews ORDER BY review_id DESC")
        rows = cursor.fetchall()
        conn.close()

        reviews = []
        total_count = len(rows)
        breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_rating_sum = 0

        for r_id, r_name, r_email, r_rating, r_text, r_created in rows:
            reviews.append({
                "review_id": r_id,
                "name": r_name,
                "email": r_email,
                "rating": r_rating,
                "review_text": r_text,
                "created_at": str(r_created) if r_created else "",
            })
            try:
                r_val = int(r_rating)
                if 1 <= r_val <= 5:
                    breakdown[r_val] += 1
                    total_rating_sum += r_val
                else:
                    breakdown[5] += 1
                    total_rating_sum += 5
            except (ValueError, TypeError):
                breakdown[5] += 1
                total_rating_sum += 5

        avg_rating = round(total_rating_sum / total_count, 1) if total_count > 0 else 0.0

        self.send_json({
            "success": True,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "total_count": total_count,
            "breakdown": breakdown,
        })

    def handle_add_review(self, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (name, email, rating, review_text) VALUES (?, ?, ?, ?)",
            (data.get("name", "Anonymous"), data.get("email", ""), data.get("rating", 5), data.get("review_text", "")),
        )
        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": "Review saved successfully!"})

    def handle_user_login(self, data):
        student_id = data.get("student_id", "")
        password = data.get("password", "")
        user = verify_user(student_id, password)
        if user:
            self.send_json({"success": True, "user": user})
        else:
            self.send_json({"success": False, "message": "Invalid Student ID or password"}, 401)

    def handle_user_register(self, data):
        success, msg = register_user(
            data.get("name", ""),
            data.get("student_id", ""),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("password", ""),
        )
        if success:
            self.send_json({"success": True, "message": msg})
        else:
            self.send_json({"success": False, "message": msg}, 400)

    def handle_admin_login(self, data):
        username = data.get("username", "")
        password = data.get("password", "")
        role = data.get("role", "")
        admin = verify_admin(username, password, role)
        if admin:
            self.send_json({"success": True, "admin": admin})
        else:
            self.send_json({"success": False, "message": "Invalid admin credentials or unauthorized role access"}, 401)

    def handle_hostel_book(self, data):
        student_id = str(data.get("student_id", "")).strip()
        if not student_id:
            self.send_json({"success": False, "message": "Student Roll ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT booking_id FROM hostel_bookings WHERE TRIM(student_id) = ? AND status IN ('Pending Approval', 'Allocated')",
            (student_id,),
        )
        if cursor.fetchone():
            conn.close()
            self.send_json(
                {"success": False, "message": "သင်သည် Hostel Booking ပြုလုပ်ထားပြီးဖြစ်သည်။ အကောင့်တစ်ခုလျှင် Booking တစ်ခုသာ တင်ခွင့်ရှိပါသည်။"},
                400,
            )
            return

        cursor.execute(
            """INSERT INTO hostel_bookings (hostel_id, student_name, student_year, student_id, national_id, payment_method, transaction_id, amount, payment_status, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', 'Pending Approval')""",
            (
                data.get("hostel_id", 1),
                data.get("student_name", ""),
                data.get("student_year", ""),
                student_id,
                data.get("nrc_id", "12/N-123456"),
                data.get("payment_method", "KBZPay (KPay QR)"),
                data.get("transaction_id", ""),
                data.get("amount", "Ks"),
            ),
        )
        cursor.execute(
            "UPDATE hostels SET available_beds = MAX(0, available_beds - 1) WHERE hostel_id = ?",
            (data.get("hostel_id", 1),),
        )
        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": "Hostel booking allocated successfully!"})

    def handle_ferry_book(self, data):
        student_id = str(data.get("student_id", "")).strip()
        if not student_id:
            self.send_json({"success": False, "message": "Student Roll ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT booking_id FROM ferry_bookings WHERE TRIM(student_id) = ? AND status IN ('Pending Approval', 'Assigned')",
            (student_id,),
        )
        if cursor.fetchone():
            conn.close()
            self.send_json(
                {"success": False, "message": "သင်သည် Ferry Ticket ရယူထားပြီးဖြစ်သည်။ အကောင့်တစ်ခုလျှင် Booking တစ်ခုသာ တင်ခွင့်ရှိပါသည်။"},
                400,
            )
            return

        cursor.execute(
            """INSERT INTO ferry_bookings (ferry_id, student_name, student_year, student_id, student_phone, payment_method, transaction_id, amount, payment_status, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', 'Pending Approval')""",
            (
                data.get("ferry_id", 1),
                data.get("student_name", ""),
                data.get("student_year", ""),
                student_id,
                data.get("student_phone", ""),
                data.get("payment_method", "KBZPay (KPay QR)"),
                data.get("transaction_id", ""),
                data.get("amount", "Ks"),
            ),
        )
        cursor.execute(
            "UPDATE ferries SET available_seats = MAX(0, available_seats - 1) WHERE ferry_id = ?",
            (data.get("ferry_id", 1),),
        )
        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": "Ferry ticket reserved successfully!"})

    def handle_inquiry(self, data):
        full_name = str(data.get("full_name", "")).strip()
        student_id = str(data.get("student_id", "")).strip()
        email = str(data.get("email", "")).strip()
        service_category = str(data.get("service_category", "")).strip()
        message = str(data.get("message", "")).strip()

        if not full_name or not student_id or not message:
            self.send_json({"success": False, "message": "အချက်အလက်များ မပြည့်စုံပါ။"}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inquiries (full_name, student_id, email, service_category, message, status) VALUES (?, ?, ?, ?, ?, ?)",
            (full_name, student_id, email, service_category, message, "Pending"),
        )
        conn.commit()
        conn.close()

        email_sent = send_gmail_notification(
            to_email=GMAIL_SENDER,
            full_name=full_name,
            student_id=student_id,
            service_category=service_category,
            message_body=message
        )
        if email_sent:
            self.send_json({"success": True, "message": "Inquiry successfully submitted and email sent!"})
        else:
            self.send_json({"success": True, "message": "Inquiry saved in database, but email notification failed to send."})

    def handle_cancel_hostel(self, data):
        student_id = str(data.get("student_id", "")).strip()
        if not student_id:
            self.send_json({"success": False, "message": "Student ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT hostel_id FROM hostel_bookings WHERE TRIM(student_id) = ? AND status != 'Cancelled' ORDER BY booking_id DESC LIMIT 1",
            (student_id,),
        )
        row = cursor.fetchone()
        if row:
            hostel_id = row[0]
            cursor.execute("DELETE FROM hostel_bookings WHERE TRIM(student_id) = ?", (student_id,))
            cursor.execute("UPDATE hostels SET available_beds = available_beds + 1 WHERE hostel_id = ?", (hostel_id,))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Hostel booking cancelled successfully!"})
        else:
            conn.close()
            self.send_json({"success": False, "message": "No active booking found"}, 400)

    def handle_cancel_ferry(self, data):
        student_id = str(data.get("student_id", "")).strip()
        if not student_id:
            self.send_json({"success": False, "message": "Student ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ferry_id FROM ferry_bookings WHERE TRIM(student_id) = ? AND status != 'Cancelled' ORDER BY booking_id DESC LIMIT 1",
            (student_id,),
        )
        row = cursor.fetchone()
        if row:
            ferry_id = row[0]
            cursor.execute("DELETE FROM ferry_bookings WHERE TRIM(student_id) = ?", (student_id,))
            cursor.execute("UPDATE ferries SET available_seats = available_seats + 1 WHERE ferry_id = ?", (ferry_id,))
            conn.commit()
            conn.close()
            self.send_json({"success": True, "message": "Ferry booking cancelled successfully!"})
        else:
            conn.close()
            self.send_json({"success": False, "message": "No active ticket found"}, 400)

    def handle_hostel_update_booking(self, data):
        booking_id = data.get("booking_id")
        hostel_id = data.get("hostel_id")
        student_name = str(data.get("student_name", "")).strip()
        student_year = str(data.get("student_year", "")).strip()
        student_id = str(data.get("student_id", "")).strip()
        national_id = str(data.get("national_id", "")).strip()
        transaction_id = str(data.get("transaction_id", "")).strip()

        if not booking_id:
            self.send_json({"success": False, "message": "Booking ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        if student_id:
            cursor.execute(
                """UPDATE hostel_bookings SET hostel_id=?, student_name=?, student_year=?, national_id=?, transaction_id=? WHERE booking_id=? AND TRIM(student_id)=?""",
                (hostel_id, student_name, student_year, national_id, transaction_id, booking_id, student_id),
            )
        else:
            cursor.execute(
                """UPDATE hostel_bookings SET hostel_id=?, student_name=?, student_year=?, national_id=?, transaction_id=? WHERE booking_id=?""",
                (hostel_id, student_name, student_year, national_id, transaction_id, booking_id),
            )
        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": "Hostel booking updated successfully!"})

    def handle_ferry_update_booking(self, data):
        booking_id = data.get("booking_id")
        ferry_id = data.get("ferry_id")
        student_name = str(data.get("student_name", "")).strip()
        student_year = str(data.get("student_year", "")).strip()
        student_id = str(data.get("student_id", "")).strip()
        student_phone = str(data.get("student_phone", "")).strip()
        transaction_id = str(data.get("transaction_id", "")).strip()

        if not booking_id:
            self.send_json({"success": False, "message": "Booking ID is required."}, 400)
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        if student_id:
            cursor.execute(
                """UPDATE ferry_bookings SET ferry_id=?, student_name=?, student_year=?, student_phone=?, transaction_id=? WHERE booking_id=? AND TRIM(student_id)=?""",
                (ferry_id, student_name, student_year, student_phone, transaction_id, booking_id, student_id),
            )
        else:
            cursor.execute(
                """UPDATE ferry_bookings SET ferry_id=?, student_name=?, student_year=?, student_phone=?, transaction_id=? WHERE booking_id=?""",
                (ferry_id, student_name, student_year, student_phone, transaction_id, booking_id),
            )
        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": "Ferry ticket updated successfully!"})

    def handle_admin_overview(self, role="", admin_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        role_clean = str(role or "").strip().lower()

        is_hostel = "hostel" in role_clean
        is_ferry = "ferry" in role_clean
        is_super = not (is_hostel or is_ferry) or "super" in role_clean

        try:
            admin_id_int = int(admin_id) if admin_id is not None and str(admin_id).isdigit() else None
        except (ValueError, TypeError):
            admin_id_int = None

        admins_list = []
        try:
            cursor.execute("SELECT id, username, name, email, role, created_at FROM admins ORDER BY id ASC")
            for aid, uname, name, email, arole, created in cursor.fetchall():
                admins_list.append({
                    "id": aid,
                    "username": uname,
                    "name": name,
                    "email": email,
                    "role": arole,
                    "created_at": str(created) if created else "",
                })
        except Exception as e:
            print(f"Error querying admins: {e}")

        hostels = []
        try:
            if is_super:
                cursor.execute(
                    "SELECT hostel_id, hostel_name, room_number, gender_type, available_beds, capacity, description, image_url, kpay_qr_url, status, admin_id FROM hostels ORDER BY hostel_id ASC"
                )
            elif is_hostel and admin_id_int:
                cursor.execute(
                    "SELECT hostel_id, hostel_name, room_number, gender_type, available_beds, capacity, description, image_url, kpay_qr_url, status, admin_id FROM hostels WHERE admin_id = ? OR admin_id IS NULL ORDER BY hostel_id ASC",
                    (admin_id_int,),
                )
            else:
                cursor.execute(
                    "SELECT hostel_id, hostel_name, room_number, gender_type, available_beds, capacity, description, image_url, kpay_qr_url, status, admin_id FROM hostels ORDER BY hostel_id ASC"
                )

            for hid, hname, rnum, gtype, abeds, cap, desc, img, kpay, st, aid in cursor.fetchall():
                hostels.append({
                    "id": hid,
                    "hostel_id": hid,
                    "name": hname,
                    "hostel_name": hname,
                    "room": rnum,
                    "room_number": rnum,
                    "gender": gtype,
                    "gender_type": gtype,
                    "available_beds": abeds,
                    "capacity": cap,
                    "description": desc,
                    "image_url": img,
                    "kpay_qr_url": kpay or "",
                    "status": st or "Active",
                    "admin_id": aid,
                })
        except Exception as e:
            print(f"Error querying hostels: {e}")

        ferry_groups = []
        try:
            if is_super:
                cursor.execute("SELECT group_id, group_name, description, admin_id FROM ferry_groups ORDER BY group_id ASC")
            elif is_ferry and admin_id_int:
                cursor.execute("SELECT group_id, group_name, description, admin_id FROM ferry_groups WHERE admin_id = ? OR admin_id IS NULL ORDER BY group_id ASC", (admin_id_int,))
            else:
                cursor.execute("SELECT group_id, group_name, description, admin_id FROM ferry_groups ORDER BY group_id ASC")

            for gid, gname, desc, aid in cursor.fetchall():
                ferry_groups.append({
                    "group_id": gid,
                    "group_name": gname,
                    "description": desc,
                    "admin_id": aid,
                })
        except Exception as e:
            print(f"Error querying ferry_groups: {e}")

        ferries = []
        try:
            if is_super:
                cursor.execute(
                    "SELECT ferry_id, group_id, ferry_name, route_name, departure_time, available_seats, capacity, kpay_qr_url, status, admin_id FROM ferries ORDER BY ferry_id ASC"
                )
            elif is_ferry and admin_id_int:
                cursor.execute(
                    "SELECT ferry_id, group_id, ferry_name, route_name, departure_time, available_seats, capacity, kpay_qr_url, status, admin_id FROM ferries WHERE admin_id = ? OR admin_id IS NULL ORDER BY ferry_id ASC",
                    (admin_id_int,),
                )
            else:
                cursor.execute(
                    "SELECT ferry_id, group_id, ferry_name, route_name, departure_time, available_seats, capacity, kpay_qr_url, status, admin_id FROM ferries ORDER BY ferry_id ASC"
                )

            for fid, gid, fname, rname, dtime, aseats, cap, kpay, st, aid in cursor.fetchall():
                ferries.append({
                    "id": fid,
                    "ferry_id": fid,
                    "group_id": gid,
                    "name": fname,
                    "ferry_name": fname,
                    "route": rname,
                    "route_name": rname,
                    "time": dtime,
                    "departure_time": dtime,
                    "available_seats": aseats,
                    "capacity": cap,
                    "kpay_qr_url": kpay or "",
                    "status": st or "Active",
                    "admin_id": aid,
                })
        except Exception as e:
            print(f"Error querying ferries: {e}")

        students = []
        try:
            cursor.execute("SELECT id, name, student_id, email, phone, role, created_at FROM users ORDER BY id ASC")
            for uid, uname, usid, uemail, uphone, urole, ucreated in cursor.fetchall():
                students.append({
                    "id": uid,
                    "name": uname,
                    "student_id": usid,
                    "email": uemail,
                    "phone": uphone,
                    "role": urole,
                    "created_at": str(ucreated) if ucreated else "",
                })
        except Exception as e:
            print(f"Error querying students: {e}")

        hostel_bookings = []
        try:
            if is_super:
                cursor.execute(
                    """SELECT hb.booking_id, hb.hostel_id, hb.student_name, hb.student_year, hb.student_id, hb.national_id, hb.payment_method, hb.transaction_id, hb.amount, hb.payment_status, hb.booking_date, hb.status, h.hostel_name, h.room_number FROM hostel_bookings hb JOIN hostels h ON hb.hostel_id = h.hostel_id ORDER BY hb.booking_id DESC"""
                )
            elif is_hostel and admin_id_int:
                cursor.execute(
                    """SELECT hb.booking_id, hb.hostel_id, hb.student_name, hb.student_year, hb.student_id, hb.national_id, hb.payment_method, hb.transaction_id, hb.amount, hb.payment_status, hb.booking_date, hb.status, h.hostel_name, h.room_number FROM hostel_bookings hb JOIN hostels h ON hb.hostel_id = h.hostel_id WHERE h.admin_id = ? OR h.admin_id IS NULL ORDER BY hb.booking_id DESC""",
                    (admin_id_int,),
                )
            else:
                cursor.execute(
                    """SELECT hb.booking_id, hb.hostel_id, hb.student_name, hb.student_year, hb.student_id, hb.national_id, hb.payment_method, hb.transaction_id, hb.amount, hb.payment_status, hb.booking_date, hb.status, h.hostel_name, h.room_number FROM hostel_bookings hb JOIN hostels h ON hb.hostel_id = h.hostel_id ORDER BY hb.booking_id DESC"""
                )

            for bid, hid, sname, syear, sid, nid, pmethod, txid, amt, payst, bdate, st, hname, rnum in cursor.fetchall():
                hostel_bookings.append({
                    "booking_id": bid,
                    "hostel_id": hid,
                    "student_name": sname,
                    "student_year": syear,
                    "student_id": sid,
                    "national_id": nid,
                    "payment_method": pmethod,
                    "transaction_id": txid,
                    "amount": amt,
                    "payment_status": payst,
                    "booking_date": str(bdate) if bdate else "",
                    "status": st,
                    "hostel_name": hname,
                    "room_number": rnum,
                })
        except Exception as e:
            print(f"Error querying hostel_bookings: {e}")

        ferry_bookings = []
        try:
            if is_super:
                cursor.execute(
                    """SELECT fb.booking_id, fb.ferry_id, fb.student_name, fb.student_year, fb.student_id, fb.student_phone, fb.payment_method, fb.transaction_id, fb.amount, fb.payment_status, fb.booking_date, fb.status, f.ferry_name, f.route_name FROM ferry_bookings fb JOIN ferries f ON fb.ferry_id = f.ferry_id ORDER BY fb.booking_id DESC"""
                )
            elif is_ferry and admin_id_int:
                cursor.execute(
                    """SELECT fb.booking_id, fb.ferry_id, fb.student_name, fb.student_year, fb.student_id, fb.student_phone, fb.payment_method, fb.transaction_id, fb.amount, fb.payment_status, fb.booking_date, fb.status, f.ferry_name, f.route_name FROM ferry_bookings fb JOIN ferries f ON fb.ferry_id = f.ferry_id WHERE f.admin_id = ? OR f.admin_id IS NULL ORDER BY fb.booking_id DESC""",
                    (admin_id_int,),
                )
            else:
                cursor.execute(
                    """SELECT fb.booking_id, fb.ferry_id, fb.student_name, fb.student_year, fb.student_id, fb.student_phone, fb.payment_method, fb.transaction_id, fb.amount, fb.payment_status, fb.booking_date, fb.status, f.ferry_name, f.route_name FROM ferry_bookings fb JOIN ferries f ON fb.ferry_id = f.ferry_id ORDER BY fb.booking_id DESC"""
                )

            for bid, fid, sname, syear, sid, sphone, pmethod, txid, amt, payst, bdate, st, fname, rname in cursor.fetchall():
                ferry_bookings.append({
                    "booking_id": bid,
                    "ferry_id": fid,
                    "student_name": sname,
                    "student_year": syear,
                    "student_id": sid,
                    "student_phone": sphone,
                    "payment_method": pmethod,
                    "transaction_id": txid,
                    "amount": amt,
                    "payment_status": payst,
                    "booking_date": str(bdate) if bdate else "",
                    "status": st,
                    "ferry_name": fname,
                    "route_name": rname,
                })
        except Exception as e:
            print(f"Error querying ferry_bookings: {e}")

        pending_payments = []
        if is_super or is_hostel:
            pending_payments += [hb for hb in hostel_bookings if hb["payment_status"] == "Pending" or hb["status"] == "Pending Approval"]
        if is_super or is_ferry:
            pending_payments += [fb for fb in ferry_bookings if fb["payment_status"] == "Pending" or fb["status"] == "Pending Approval"]

        inquiries = []
        try:
            if is_super:
                cursor.execute("SELECT inquiry_id, full_name, student_id, email, service_category, message, status, created_at FROM inquiries ORDER BY inquiry_id DESC")
            elif is_hostel:
                cursor.execute("SELECT inquiry_id, full_name, student_id, email, service_category, message, status, created_at FROM inquiries WHERE service_category LIKE '%Hostel%' ORDER BY inquiry_id DESC")
            elif is_ferry:
                cursor.execute("SELECT inquiry_id, full_name, student_id, email, service_category, message, status, created_at FROM inquiries WHERE service_category LIKE '%Ferry%' ORDER BY inquiry_id DESC")
            else:
                cursor.execute("SELECT inquiry_id, full_name, student_id, email, service_category, message, status, created_at FROM inquiries ORDER BY inquiry_id DESC")

            for inq_id, fname, sid, uemail, scat, msg, st, created in cursor.fetchall():
                inquiries.append({
                    "inquiry_id": inq_id,
                    "full_name": fname,
                    "student_id": sid,
                    "email": uemail or "",
                    "service_category": scat,
                    "message": msg,
                    "status": st,
                    "created_at": str(created) if created else "",
                })
        except Exception as e:
            print(f"Error querying inquiries: {e}")

        conn.close()

        self.send_json({
            "success": True,
            "role": "super_admin" if is_super else ("hostel" if is_hostel else "ferry"),
            "admin_id": admin_id_int,
            "admins": admins_list,
            "pending_payments_count": len(pending_payments),
            "pending_payments": pending_payments,
            "hostels": hostels,
            "ferry_groups": ferry_groups,
            "ferries": ferries,
            "students": students,
            "hostel_bookings": hostel_bookings,
            "ferry_bookings": ferry_bookings,
            "inquiries": inquiries,
        })

    def handle_admin_confirm_payment(self, data):
        btype = data.get("booking_type")
        bid = data.get("booking_id")
        action = data.get("action")

        conn = get_db_connection()
        cursor = conn.cursor()

        if btype == "hostel":
            new_status = "Allocated" if action == "approve" else "Rejected"
            new_pay_status = "Confirmed" if action == "approve" else "Rejected"
            cursor.execute(
                "UPDATE hostel_bookings SET status=?, payment_status=? WHERE booking_id=?",
                (new_status, new_pay_status, bid),
            )
            if action == "reject":
                cursor.execute(
                    "UPDATE hostels SET available_beds = available_beds + 1 WHERE hostel_id = (SELECT hostel_id FROM hostel_bookings WHERE booking_id=?)",
                    (bid,),
                )
        elif btype == "ferry":
            new_status = "Assigned" if action == "approve" else "Rejected"
            new_pay_status = "Confirmed" if action == "approve" else "Rejected"
            cursor.execute(
                "UPDATE ferry_bookings SET status=?, payment_status=? WHERE booking_id=?",
                (new_status, new_pay_status, bid),
            )
            if action == "reject":
                cursor.execute(
                    "UPDATE ferries SET available_seats = available_seats + 1 WHERE ferry_id = (SELECT ferry_id FROM ferry_bookings WHERE booking_id=?)",
                    (bid,),
                )

        conn.commit()
        conn.close()
        self.send_json({"success": True, "message": f"Payment {action}d successfully!"})


def run_server(port=int(os.environ.get("PORT", 8080))):
    init_sqlite_db()
    server_address = ("", port)
    httpd = HTTPServer(server_address, UTYCCPortalHandler)
    print(f"UTYCC Portal Server running on http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()