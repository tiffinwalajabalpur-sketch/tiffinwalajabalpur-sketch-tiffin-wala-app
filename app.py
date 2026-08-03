"""
Tiffin Wala - Lead-to-Booking Automation System
A Flask web application for managing tiffin subscription orders.
"""

import os
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, send_from_directory, session, abort
)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# ────────────────────────────────────────────────────────────────────────────
# APP INITIALIZATION
# ────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tw-super-secret-key-change-in-production-2024')

# ────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER     = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Admin credentials — use environment variables in production
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'TiffinWala@2024')

# Database and Discord configuration
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')  # Set automatically by Render
db_url = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'tiffin.db')}")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config.update(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,   # 5 MB max upload
    SQLALCHEMY_DATABASE_URI=db_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

db = SQLAlchemy(app)

# ────────────────────────────────────────────────────────────────────────────
# DATABASE MODELS
# ────────────────────────────────────────────────────────────────────────────

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    whatsapp_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    customer_type = db.Column(db.String(50), nullable=False, default='Irregular')
    plan_type = db.Column(db.String(50))
    thali_type = db.Column(db.String(50), nullable=False)
    meal_time = db.Column(db.String(50), nullable=False)
    delivery_area = db.Column(db.String(100), nullable=False, default='Not Specified')
    booking_dates = db.Column(db.Text, nullable=False, default='Not Specified')
    total_amount = db.Column(db.Float, nullable=False)
    map_link = db.Column(db.String(500))
    order_status = db.Column(db.String(50), nullable=False, default='Pending')
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

def init_db() -> None:
    """Create the database and tables if they don't exist."""
    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with app.app_context():
        db.create_all()

# ────────────────────────────────────────────────────────────────────────────
# PRICING MATRIX & DELIVERY AREAS
# ────────────────────────────────────────────────────────────────────────────

VALID_AREAS = [
    'Adhartal', 'Damoh Naka', 'Napier Town', 'Wright Town', 
    'Vijay Nagar', 'Ranital', 'Sneh Nagar', 'Madan Mahal', 'Ghanta Ghar Area'
]

VALID_PRICES: dict[tuple[str, str], int] = {
    ('Regular',   'regular'): 60,
    ('Regular',   'premium'): 120,
    ('Irregular', 'regular'): 80,
    ('Irregular', 'premium'): 120,
}

# ────────────────────────────────────────────────────────────────────────────
# WHATSAPP AUTOMATION PLACEHOLDER
# ────────────────────────────────────────────────────────────────────────────

def log_new_booking(order_id: int, customer_name: str, phone_number: str,
                    plan: str, thali: str, meal_time: str, amount: float) -> None:
    print("\n" + "="*60)
    print(f"[NEW ORDER #{order_id}] {customer_name} (+91{phone_number})")
    print(f"  Plan: {plan} | Thali: {thali} | Time: {meal_time} | Rs.{amount}")
    print("  Customer will reach you on WhatsApp to complete payment.")
    print("="*60 + "\n")

def send_discord_reminder(meal_time: str):
    if not DISCORD_WEBHOOK_URL:
        return
    with app.app_context():
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        orders = Order.query.filter(
            Order.timestamp >= today_start, 
            Order.timestamp <= today_end,
            Order.meal_time == meal_time,
            Order.order_status == 'Confirmed'
        ).all()
        
        if orders:
            content = f"🛵 **Delivery Reminder!**\nYou have **{len(orders)} {meal_time.title()}** orders ready for delivery right now.\n👉 Check your Admin Dashboard!"
            try:
                requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
            except Exception as e:
                print(f"[Discord Error] {e}")

# Keep-alive pinger — prevents Render free tier from sleeping
def keep_alive():
    url = RENDER_EXTERNAL_URL or 'http://localhost:5000'
    try:
        requests.get(url + '/ping', timeout=10)
        print(f"[Keep-Alive] Pinged {url}/ping successfully.")
    except Exception as e:
        print(f"[Keep-Alive] Ping failed: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=send_discord_reminder, args=['lunch'],  trigger="cron", hour=10, minute=0)
scheduler.add_job(func=send_discord_reminder, args=['dinner'], trigger="cron", hour=18, minute=0)
scheduler.add_job(func=keep_alive, trigger="interval", minutes=10)
scheduler.start()

# ────────────────────────────────────────────────────────────────────────────
# UTILITY HELPERS
# ────────────────────────────────────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def get_order_stats() -> dict:
    """Return aggregate stats for the admin dashboard."""
    total = db.session.query(func.count(Order.id)).scalar() or 0
    pending = db.session.query(func.count(Order.id)).filter(Order.order_status == 'Pending').scalar() or 0
    confirmed = db.session.query(func.count(Order.id)).filter(Order.order_status.in_(['Confirmed', 'Delivered'])).scalar() or 0
    revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.order_status.in_(['Confirmed', 'Delivered'])).scalar() or 0
    
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    today = db.session.query(func.count(Order.id)).filter(Order.timestamp >= today_start, Order.timestamp <= today_end).scalar() or 0
    today_revenue = db.session.query(func.sum(Order.total_amount)).filter(Order.order_status.in_(['Confirmed', 'Delivered']), Order.timestamp >= today_start, Order.timestamp <= today_end).scalar() or 0
    
    return dict(total=total, pending=pending, confirmed=confirmed,
                revenue=revenue, today=today, today_revenue=today_revenue)

# ────────────────────────────────────────────────────────────────────────────
# ROUTES — PUBLIC
# ────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    """Health-check endpoint used by the keep-alive scheduler to prevent Render from sleeping."""
    return 'pong', 200

@app.route('/submit-order', methods=['POST'])
def submit_order():
    try:
        customer_name   = request.form.get('customer_name',   '').strip()
        whatsapp_number = request.form.get('whatsapp_number', '').strip()
        address         = request.form.get('address',         '').strip()
        customer_type   = request.form.get('customer_type',   '').strip()
        thali_type      = request.form.get('thali_type',      '').strip()
        meal_time       = request.form.get('meal_time',       '').strip()
        delivery_area   = request.form.get('delivery_area',   '').strip()
        booking_dates   = request.form.get('booking_dates',   '').strip()
        map_link        = request.form.get('map_link',        '').strip()

        try:
            total_amount = float(request.form.get('total_amount', 0))
        except ValueError:
            return jsonify(success=False, message='Invalid amount.'), 400

        errors = []
        if not customer_name: errors.append('Full name is required.')
        if not whatsapp_number or not whatsapp_number.isdigit() or len(whatsapp_number) != 10:
            errors.append('Valid 10-digit WhatsApp number is required.')
        if not address: errors.append('Delivery address is required.')
        if customer_type not in ('Regular', 'Irregular', 'A La Carte'): errors.append('Invalid customer type.')
        if thali_type not in ('regular', 'premium', 'A La Carte'): errors.append('Invalid thali type.')
        if meal_time not in ('lunch', 'dinner'): errors.append('Invalid meal time.')
        if delivery_area not in VALID_AREAS: errors.append('Invalid or unsupported delivery area.')
        if not booking_dates: errors.append('Please select at least one booking date.')
        if errors: return jsonify(success=False, message=' '.join(errors)), 400

        # Validate price for standard meals
        if thali_type != 'A La Carte':
            base_price = VALID_PRICES.get((customer_type, thali_type))
            num_dates = len([d for d in booking_dates.split(',') if d.strip()])
            expected_price = base_price * num_dates if base_price else None
            
            if expected_price is None or int(total_amount) != expected_price:
                return jsonify(
                    success=False,
                    message=f'Price mismatch. Expected Rs.{expected_price} for '
                            f'{customer_type} customer with {thali_type.title()} Thali over {num_dates} days.'
                ), 400

        if customer_type == 'Regular':
            existing = Order.query.filter_by(whatsapp_number=whatsapp_number, customer_type='Regular').first()
            if existing:
                return jsonify(
                    success=False,
                    message='You have already claimed your Trial! Please select "Irregular / One-Time Booking" or contact us to start your monthly subscription.'
                ), 400

        new_order = Order(
            customer_name=customer_name,
            whatsapp_number=whatsapp_number,
            address=address,
            customer_type=customer_type,
            thali_type=thali_type,
            meal_time=meal_time,
            delivery_area=delivery_area,
            booking_dates=booking_dates,
            total_amount=total_amount,
            map_link=map_link
        )
        db.session.add(new_order)
        db.session.commit()
        order_id = new_order.id

        log_new_booking(
            order_id, customer_name, whatsapp_number,
            customer_type, thali_type, meal_time, total_amount
        )

        return jsonify(
            success=True,
            message=f'Order #{order_id} placed! Please complete payment via WhatsApp.',
            order_id=order_id
        )

    except Exception as exc:
        print(f"[ERROR] submit_order: {exc}")
        return jsonify(success=False, message='Something went wrong. Please try again.'), 500

# ────────────────────────────────────────────────────────────────────────────
# ROUTES — ADMIN
# ────────────────────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = False
            return redirect(url_for('admin_dashboard'))
        error = 'Invalid credentials. Please try again.'

    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    orders = Order.query.order_by(Order.timestamp.desc()).all()
    
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    today_orders = Order.query.filter(Order.timestamp >= today_start, Order.timestamp <= today_end).order_by(Order.timestamp.desc()).all()
    
    stats = get_order_stats()
    return render_template('admin.html', orders=orders, stats=stats, today_orders=today_orders)

@app.route('/admin/update-status/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id: int):
    new_status = request.form.get('status', 'Confirmed')
    if new_status not in ('Pending', 'Confirmed', 'Delivered', 'Cancelled'):
        abort(400)
    
    order = db.session.get(Order, order_id)
    if order:
        order.order_status = new_status
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/screenshot/<path:filename>')
@admin_required
def serve_screenshot(filename: str):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    print(f"\n[Tiffin Wala] Starting on http://0.0.0.0:{port}")
    print(f"[Admin] Panel: http://0.0.0.0:{port}/admin/login")
    print(f"        Username: {ADMIN_USERNAME} | Password: {ADMIN_PASSWORD}\n")
    app.run(debug=debug, host='0.0.0.0', port=port)
