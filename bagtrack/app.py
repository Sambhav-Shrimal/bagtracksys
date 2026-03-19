"""
BagTrack - Production Management System
A piece-rate tracking system for paper bag manufacturing workers
SQLite version for Render.com deployment
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
import os
import secrets

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
# SQLite database file


app.config['DATABASE'] = os.environ.get('DATABASE', 'bagtrack.db')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# SQLite connection function
def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

# Create upload folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'production'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'payments'), exist_ok=True)


# Initialize SQLite database
def init_db():
    """Initialize the database with schema"""
    db = get_db()
    cursor = db.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS production (
            production_id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            bag_type TEXT,
            quantity INTEGER NOT NULL,
            rate REAL NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'SUBMITTED',
            rejection_reason TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE CASCADE,
            FOREIGN KEY (reviewed_by) REFERENCES workers(worker_id) ON DELETE SET NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            transaction_reference TEXT,
            payment_screenshot TEXT,
            status TEXT DEFAULT 'PAYMENT_SENT',
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confirmed_at TIMESTAMP,
            paid_by INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY (worker_id) REFERENCES workers(worker_id) ON DELETE CASCADE,
            FOREIGN KEY (paid_by) REFERENCES workers(worker_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_production_links (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER NOT NULL,
            production_id INTEGER NOT NULL,
            amount_allocated REAL NOT NULL,
            FOREIGN KEY (payment_id) REFERENCES payments(payment_id) ON DELETE CASCADE,
            FOREIGN KEY (production_id) REFERENCES production(production_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES workers(worker_id) ON DELETE CASCADE
        )
    ''')
    
    # Check if admin user exists
    cursor.execute("SELECT COUNT(*) as count FROM workers WHERE is_admin = 1")
    result = cursor.fetchone()
    if result[0] == 0:
        # Create default admin user
        password_hash = generate_password_hash('9vvb70cz5h')
        cursor.execute("""
            INSERT INTO workers (name, phone_number, password_hash, is_admin)
            VALUES (?, ?, ?, 1)
        """, ('Admin', '9986109356', password_hash))
    
    db.commit()
    cursor.close()
    db.close()


# Initialize database on startup
init_db()


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('worker_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def log_activity(action, entity_type, entity_id, details=None):
    """Log user activity for audit trail"""
    try:
        db = get_db()
        cursor = db.cursor()
        ip_address = request.remote_addr
        user_id = session.get('user_id')
        
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, entity_type, entity_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, entity_type, entity_id, details, ip_address))
        
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Activity log error: {e}")


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page - redirect based on login status"""
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('worker_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        phone_number = request.form.get('phone_number', '').strip()
        password = request.form.get('password', '')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT worker_id, name, password_hash, is_admin, is_active 
            FROM workers 
            WHERE phone_number = ?
        """, (phone_number,))
        
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user and user['is_active'] and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['worker_id']
            session['name'] = user['name']
            session['is_admin'] = user['is_admin']
            
            log_activity('LOGIN', 'user', user['worker_id'], 'User logged in')
            
            flash(f'Welcome back, {user["name"]}!', 'success')
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('worker_dashboard'))
        else:
            flash('Invalid phone number or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    log_activity('LOGOUT', 'user', session['user_id'], 'User logged out')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Worker registration (can be disabled in production)"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        password = request.form.get('password', '')
        
        if not all([name, phone_number, password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        db = get_db()
        cursor = db.cursor()
        
        # Check if phone number already exists
        cursor.execute("SELECT worker_id FROM workers WHERE phone_number = ?", (phone_number,))
        if cursor.fetchone():
            flash('Phone number already registered.', 'danger')
            cursor.close()
            db.close()
            return render_template('register.html')
        
        # Create new worker
        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO workers (name, phone_number, password_hash, is_admin)
            VALUES (?, ?, ?, 0)
        """, (name, phone_number, password_hash))
        
        db.commit()
        worker_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        log_activity('REGISTER', 'user', worker_id, f'New worker registered: {name}')
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


# ============================================================================
# WORKER DASHBOARD & ROUTES
# ============================================================================

@app.route('/worker/dashboard')
@login_required
def worker_dashboard():
    """Worker dashboard showing summary and quick actions"""
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    worker_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Get worker summary statistics
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN status IN ('APPROVED', 'PAYMENT_SENT', 'PAYMENT_RECEIVED') THEN total_amount ELSE 0 END), 0) as total_approved,
            COALESCE(SUM(CASE WHEN status = 'PAYMENT_RECEIVED' THEN total_amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN status IN ('APPROVED', 'PAYMENT_SENT') THEN total_amount ELSE 0 END), 0) as total_pending
        FROM production
        WHERE worker_id = ?
    """, (worker_id,))
    
    summary = cursor.fetchone()
    
    # Get recent production submissions
    cursor.execute("""
        SELECT production_id, photo_path, bag_type, quantity, rate, total_amount, status, submitted_at
        FROM production
        WHERE worker_id = ?
        ORDER BY submitted_at DESC
        LIMIT 10
    """, (worker_id,))
    
    recent_submissions = cursor.fetchall()
    
    # Get pending payment confirmations
    cursor.execute("""
        SELECT payment_id, amount, payment_method, transaction_reference, paid_at
        FROM payments
        WHERE worker_id = ? AND status = 'PAYMENT_SENT'
        ORDER BY paid_at DESC
    """, (worker_id,))
    
    pending_payments = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('worker_dashboard.html', 
                          summary=summary, 
                          recent_submissions=recent_submissions,
                          pending_payments=pending_payments)


@app.route('/worker/submit-production', methods=['GET', 'POST'])
@login_required
def submit_production():
    """Worker submits new production entry"""
    if session.get('is_admin'):
        flash('Admin users cannot submit production.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        worker_id = session['user_id']
        bag_type = request.form.get('bag_type', '').strip()
        quantity = request.form.get('quantity', type=int)
        rate = request.form.get('rate', type=float)
        photo = request.files.get('photo')
        
        # Validation
        if not quantity or quantity <= 0:
            flash('Please enter a valid quantity.', 'danger')
            return render_template('submit_production.html')
        
        if not rate or rate <= 0:
            flash('Please enter a valid rate.', 'danger')
            return render_template('submit_production.html')
        
        if not photo or not allowed_file(photo.filename):
            flash('Please upload a valid photo (PNG, JPG, JPEG, GIF, WEBP).', 'danger')
            return render_template('submit_production.html')
        
        # Save photo
        filename = secure_filename(photo.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{worker_id}_{timestamp}_{filename}"
        photo_path = f'production/{unique_filename}'
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_path)
        photo.save(full_path)
        
        # Calculate total
        total_amount = quantity * rate
        
        # Insert production record
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO production (worker_id, photo_path, bag_type, quantity, rate, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, 'SUBMITTED')
        """, (worker_id, photo_path, bag_type or None, quantity, rate, total_amount))
        
        db.commit()
        production_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        log_activity('SUBMIT_PRODUCTION', 'production', production_id, 
                    f'Submitted: {quantity} bags @ ₹{rate} = ₹{total_amount}')
        
        flash(f'Production submitted successfully! Total: ₹{total_amount:.2f}', 'success')
        return redirect(url_for('worker_dashboard'))
    
    return render_template('submit_production.html')


@app.route('/worker/production-history')
@login_required
def production_history():
    """View all production submissions for worker"""
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    worker_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT production_id, photo_path, bag_type, quantity, rate, total_amount, 
               status, rejection_reason, submitted_at, reviewed_at
        FROM production
        WHERE worker_id = ?
        ORDER BY submitted_at DESC
    """, (worker_id,))
    
    productions = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('production_history.html', productions=productions)


@app.route('/worker/confirm-payment/<int:payment_id>', methods=['POST'])
@login_required
def confirm_payment(payment_id):
    """Worker confirms payment has been received"""
    if session.get('is_admin'):
        flash('Admin users cannot confirm payments.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    worker_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    
    # Verify payment belongs to this worker and is in PAYMENT_SENT status
    cursor.execute("""
        SELECT payment_id FROM payments
        WHERE payment_id = ? AND worker_id = ? AND status = 'PAYMENT_SENT'
    """, (payment_id, worker_id))
    
    payment = cursor.fetchone()
    
    if not payment:
        flash('Payment not found or already confirmed.', 'danger')
        cursor.close()
        db.close()
        return redirect(url_for('worker_dashboard'))
    
    # Update payment status
    cursor.execute("""
        UPDATE payments
        SET status = 'PAYMENT_RECEIVED', confirmed_at = CURRENT_TIMESTAMP
        WHERE payment_id = ?
    """, (payment_id,))
    
    # Update related production entries (SQLite compatible)
    cursor.execute("""
        UPDATE production 
        SET status = 'PAYMENT_RECEIVED'
        WHERE production_id IN (
            SELECT production_id FROM payment_production_links WHERE payment_id = ?
        ) AND status = 'PAYMENT_SENT'
    """, (payment_id,))
    
    db.commit()
    cursor.close()
    db.close()
    
    log_activity('CONFIRM_PAYMENT', 'payment', payment_id, 'Worker confirmed payment received')
    
    flash('Payment confirmed successfully!', 'success')
    return redirect(url_for('worker_dashboard'))


# ============================================================================
# ADMIN DASHBOARD & ROUTES
# ============================================================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with overview statistics"""
    db = get_db()
    cursor = db.cursor()
    
    # Get overall statistics
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT w.worker_id) as total_workers,
            COALESCE(SUM(CASE WHEN p.status IN ('APPROVED', 'PAYMENT_SENT', 'PAYMENT_RECEIVED') THEN p.total_amount ELSE 0 END), 0) as total_production_value,
            COALESCE(SUM(CASE WHEN pay.status = 'PAYMENT_RECEIVED' THEN pay.amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN p.status IN ('APPROVED', 'PAYMENT_SENT') THEN p.total_amount ELSE 0 END), 0) as total_pending
        FROM workers w
        LEFT JOIN production p ON w.worker_id = p.worker_id
        LEFT JOIN payments pay ON w.worker_id = pay.worker_id
        WHERE w.is_admin = 0
    """)
    
    stats = cursor.fetchone()
    
    # Get worker summaries
    cursor.execute("""
        SELECT 
            w.worker_id,
            w.name,
            w.phone_number,
            COALESCE(SUM(CASE WHEN p.status IN ('APPROVED', 'PAYMENT_SENT', 'PAYMENT_RECEIVED') THEN p.total_amount ELSE 0 END), 0) as total_approved,
            COALESCE(SUM(CASE WHEN pay.status = 'PAYMENT_RECEIVED' THEN pay.amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN p.status IN ('APPROVED', 'PAYMENT_SENT') THEN p.total_amount ELSE 0 END), 0) as total_pending
        FROM workers w
        LEFT JOIN production p ON w.worker_id = p.worker_id
        LEFT JOIN payments pay ON w.worker_id = pay.worker_id
        WHERE w.is_admin = 0 AND w.is_active = 1
        GROUP BY w.worker_id, w.name, w.phone_number
        ORDER BY w.name
    """)
    
    workers = cursor.fetchall()
    
    # Get pending submissions
    cursor.execute("""
        SELECT p.production_id, w.name as worker_name, p.photo_path, p.bag_type, 
               p.quantity, p.rate, p.total_amount, p.submitted_at
        FROM production p
        INNER JOIN workers w ON p.worker_id = w.worker_id
        WHERE p.status = 'SUBMITTED'
        ORDER BY p.submitted_at ASC
    """)
    
    pending_submissions = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('admin_dashboard.html', 
                          stats=stats, 
                          workers=workers,
                          pending_submissions=pending_submissions)


@app.route('/admin/production-log')
@admin_required
def production_log():
    """View all production submissions with filters"""
    # Get filter parameters
    worker_id = request.args.get('worker_id', type=int)
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    db = get_db()
    cursor = db.cursor()
    
    # Build query
    query = """
        SELECT p.production_id, w.name as worker_name, p.photo_path, p.bag_type,
               p.quantity, p.rate, p.total_amount, p.status, p.submitted_at, 
               p.reviewed_at, r.name as reviewed_by_name
        FROM production p
        INNER JOIN workers w ON p.worker_id = w.worker_id
        LEFT JOIN workers r ON p.reviewed_by = r.worker_id
        WHERE 1=1
    """
    params = []
    
    if worker_id:
        query += " AND p.worker_id = ?"
        params.append(worker_id)
    
    if status:
        query += " AND p.status = ?"
        params.append(status)
    
    if date_from:
        query += " AND DATE(p.submitted_at) >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(p.submitted_at) <= ?"
        params.append(date_to)
    
    query += " ORDER BY p.submitted_at DESC"
    
    cursor.execute(query, params)
    productions = cursor.fetchall()
    
    # Get all workers for filter dropdown
    cursor.execute("SELECT worker_id, name FROM workers WHERE is_admin = 0 ORDER BY name")
    workers = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('production_log.html', 
                          productions=productions, 
                          workers=workers,
                          filters={'worker_id': worker_id, 'status': status, 
                                  'date_from': date_from, 'date_to': date_to})


@app.route('/admin/review-production/<int:production_id>', methods=['GET', 'POST'])
@admin_required
def review_production(production_id):
    """Admin reviews and approves/rejects production submission"""
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        rejection_reason = request.form.get('rejection_reason', '').strip()
        
        if action == 'approve':
            cursor.execute("""
                UPDATE production
                SET status = 'APPROVED', reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
                WHERE production_id = ? AND status = 'SUBMITTED'
            """, (session['user_id'], production_id))
            
            db.commit()
            log_activity('APPROVE_PRODUCTION', 'production', production_id, 'Production approved')
            flash('Production approved successfully!', 'success')
            
        elif action == 'reject':
            if not rejection_reason:
                flash('Please provide a rejection reason.', 'danger')
                cursor.close()
                db.close()
                return redirect(url_for('review_production', production_id=production_id))
            
            cursor.execute("""
                UPDATE production
                SET status = 'REJECTED', rejection_reason = ?, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
                WHERE production_id = ? AND status = 'SUBMITTED'
            """, (rejection_reason, session['user_id'], production_id))
            
            db.commit()
            log_activity('REJECT_PRODUCTION', 'production', production_id, f'Rejected: {rejection_reason}')
            flash('Production rejected.', 'info')
        
        cursor.close()
        db.close()
        return redirect(url_for('admin_dashboard'))
    
    # GET request - show production details
    cursor.execute("""
        SELECT p.*, w.name as worker_name
        FROM production p
        INNER JOIN workers w ON p.worker_id = w.worker_id
        WHERE p.production_id = ?
    """, (production_id,))
    
    production = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not production:
        flash('Production not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('review_production.html', production=production)


@app.route('/admin/record-payment', methods=['GET', 'POST'])
@admin_required
def record_payment():
    """Admin records a payment made to worker"""
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        worker_id = request.form.get('worker_id', type=int)
        amount = request.form.get('amount', type=float)
        payment_method = request.form.get('payment_method')
        transaction_reference = request.form.get('transaction_reference', '').strip()
        notes = request.form.get('notes', '').strip()
        screenshot = request.files.get('screenshot')
        
        # Validation
        if not worker_id or not amount or amount <= 0 or not payment_method:
            flash('Please fill in all required fields.', 'danger')
            cursor.close()
            db.close()
            return redirect(url_for('record_payment'))
        
        # Handle screenshot upload
        screenshot_path = None
        if screenshot and allowed_file(screenshot.filename):
            filename = secure_filename(screenshot.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"payment_{worker_id}_{timestamp}_{filename}"
            screenshot_path = f'payments/{unique_filename}'
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], screenshot_path)
            screenshot.save(full_path)
        
        # Insert payment record
        cursor.execute("""
            INSERT INTO payments (worker_id, amount, payment_method, transaction_reference, 
                                 payment_screenshot, paid_by, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'PAYMENT_SENT')
        """, (worker_id, amount, payment_method, transaction_reference or None, 
              screenshot_path, session['user_id'], notes or None))
        
        payment_id = cursor.lastrowid
        
        # Link payment to approved production entries
        cursor.execute("""
            SELECT production_id, total_amount
            FROM production
            WHERE worker_id = ? AND status = 'APPROVED'
            ORDER BY submitted_at ASC
        """, (worker_id,))
        
        approved_productions = cursor.fetchall()
        remaining_amount = amount
        
        for prod in approved_productions:
            if remaining_amount <= 0:
                break
            
            allocated = min(remaining_amount, prod['total_amount'])
            
            cursor.execute("""
                INSERT INTO payment_production_links (payment_id, production_id, amount_allocated)
                VALUES (?, ?, ?)
            """, (payment_id, prod['production_id'], allocated))
            
            # Update production status to PAYMENT_SENT
            cursor.execute("""
                UPDATE production
                SET status = 'PAYMENT_SENT'
                WHERE production_id = ?
            """, (prod['production_id'],))
            
            remaining_amount -= allocated
        
        db.commit()
        cursor.close()
        db.close()
        
        log_activity('RECORD_PAYMENT', 'payment', payment_id, 
                    f'Recorded payment of ₹{amount} to worker {worker_id}')
        
        flash(f'Payment of ₹{amount:.2f} recorded successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # GET request - show payment form
    cursor.execute("""
        SELECT w.worker_id, w.name, 
               COALESCE(SUM(CASE WHEN p.status = 'APPROVED' THEN p.total_amount ELSE 0 END), 0) as pending_amount
        FROM workers w
        LEFT JOIN production p ON w.worker_id = p.worker_id
        WHERE w.is_admin = 0 AND w.is_active = 1
        GROUP BY w.worker_id, w.name
        HAVING pending_amount > 0
        ORDER BY w.name
    """)
    
    workers = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('record_payment.html', workers=workers)


@app.route('/admin/payment-log')
@admin_required
def payment_log():
    """View all payment records"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT pay.payment_id, w.name as worker_name, pay.amount, pay.payment_method,
               pay.transaction_reference, pay.status, pay.paid_at, pay.confirmed_at,
               pb.name as paid_by_name
        FROM payments pay
        INNER JOIN workers w ON pay.worker_id = w.worker_id
        INNER JOIN workers pb ON pay.paid_by = pb.worker_id
        ORDER BY pay.paid_at DESC
    """)
    
    payments = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('payment_log.html', payments=payments)


@app.route('/admin/worker-details/<int:worker_id>')
@admin_required
def worker_details(worker_id):
    """View detailed information about a specific worker"""
    db = get_db()
    cursor = db.cursor()
    
    # Get worker info
    cursor.execute("""
        SELECT worker_id, name, phone_number, created_at
        FROM workers
        WHERE worker_id = ? AND is_admin = 0
    """, (worker_id,))
    
    worker = cursor.fetchone()
    
    if not worker:
        flash('Worker not found.', 'danger')
        cursor.close()
        db.close()
        return redirect(url_for('admin_dashboard'))
    
    # Get production summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_submissions,
            COALESCE(SUM(CASE WHEN status IN ('APPROVED', 'PAYMENT_SENT', 'PAYMENT_RECEIVED') THEN total_amount ELSE 0 END), 0) as total_approved,
            COALESCE(SUM(CASE WHEN status = 'PAYMENT_RECEIVED' THEN total_amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN status IN ('APPROVED', 'PAYMENT_SENT') THEN total_amount ELSE 0 END), 0) as total_pending,
            COALESCE(SUM(CASE WHEN status = 'SUBMITTED' THEN 1 ELSE 0 END), 0) as pending_review,
            COALESCE(SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END), 0) as rejected_count
        FROM production
        WHERE worker_id = ?
    """, (worker_id,))
    
    production_summary = cursor.fetchone()
    
    # Get recent productions
    cursor.execute("""
        SELECT production_id, photo_path, bag_type, quantity, rate, total_amount, status, submitted_at
        FROM production
        WHERE worker_id = ?
        ORDER BY submitted_at DESC
        LIMIT 20
    """, (worker_id,))
    
    productions = cursor.fetchall()
    
    # Get payment history
    cursor.execute("""
        SELECT payment_id, amount, payment_method, transaction_reference, status, paid_at, confirmed_at
        FROM payments
        WHERE worker_id = ?
        ORDER BY paid_at DESC
    """, (worker_id,))
    
    payments = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('worker_details.html', 
                          worker=worker, 
                          production_summary=production_summary,
                          productions=productions,
                          payments=payments)


# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/worker-pending/<int:worker_id>')
@admin_required
def api_worker_pending(worker_id):
    """API endpoint to get worker's pending amount"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN status = 'APPROVED' THEN total_amount ELSE 0 END), 0) as pending_amount
        FROM production
        WHERE worker_id = ?
    """, (worker_id,))
    
    result = cursor.fetchone()
    cursor.close()
    db.close()
    
    return jsonify({'pending_amount': float(result['pending_amount'])})


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
