# app.py
# set FLASK_ENV=development 
# set FLASK_ENV=production

from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user # Removed LoginManager here
from datetime import datetime, date
from extensions import db, login_manager # Keep this import
import pytz
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SOA_FOLDER'] = 'static/soa'
app.config['ENV_MODE'] = os.getenv('FLASK_ENV', 'development')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SOA_FOLDER'], exist_ok=True)

# Initialize extensions (using the instances imported from extensions.py)
# This MUST happen after app.config is set
db.init_app(app)
login_manager.init_app(app) # This is the correct instance imported from extensions.py

# Configure login_manager AFTER it has been initialized with the app
login_manager.login_view = 'cx_login'  # <-- your login route function name

# Initialize Flask-Migrate (requires both app and db instances)
migrate = Migrate(app, db) # This should come after db.init_app(app)


# Import models after db is ready
from models import Cx, PaymentProof, CxRequest

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Cx, int(user_id))


# ===== Routes (These remain exactly as you had them, no change needed here from your previous app.py) =====
@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/cx/login', methods=['GET', 'POST'])
def cx_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Cx.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('cx_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('cx/login.html')

@app.route('/cx/register', methods=['GET', 'POST'])
def cx_register():
    if request.method == 'POST':
        # Get form values
        surname = request.form.get('surname')
        first_name = request.form.get('first_name')
        middle_initial = request.form.get('middle_initial', '')
        extension_name = request.form.get('extension_name', '')

        account_number = request.form.get('account_number')
        internet_plan = request.form.get('internet_plan')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('cx/register.html')

        # Check if email already exists
        existing_user = Cx.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists.', 'warning')
            return render_template('cx/register.html')

        # Create full name for 'name' attribute
        # Using middle_initial for middle_name in the display name as per user's previous preference
        full_name = f"{first_name} {middle_initial + '.' if middle_initial else ''} {surname} {extension_name}".strip()

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create new user object
        new_user = Cx(
            name=full_name,
            email=email,
            password=hashed_password,
            account_number=account_number,
            internet_plan=internet_plan,
            # Assigning individual name components to their respective columns
            first_name=first_name,
            # Map middle_initial from registration to middle_name for profile display
            middle_name=middle_initial, # Saving middle_initial to middle_name
            middle_initial=middle_initial, # Keeping middle_initial column populated too
            surname=surname,
            extension_name=extension_name # Saving extension_name
        )

        # Save to DB
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('cx_login'))

    return render_template('cx/register.html')




def calculate_age(birthdate):
    if birthdate:
        today = date.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return None
    
    
@app.route('/cx/dashboard')
@login_required
def cx_dashboard():
    tab = request.args.get('tab', 'home')
    age = calculate_age(current_user.birthdate)
    uploads = PaymentProof.query.filter_by(cx_id=current_user.id).order_by(PaymentProof.uploaded_at.desc()).all()
    requests = CxRequest.query.filter_by(cx_id=current_user.id).order_by(CxRequest.created_at.desc()).all()
    
    
    return render_template(
        'cx/dashboard.html',
        active_tab=tab,
        tab=tab, age=age,
        dashboard_header=True,
        previous_uploads=uploads,
        user_requests=requests,
        now=datetime.now()
    )

@app.route('/cx/upload', methods=['POST'])
@login_required
def upload_proof():
    file = request.files.get('proof_file')
    reference_number = request.form.get('reference_number')
    amount = request.form.get('amount')
    payment_date_raw = request.form.get('payment_date')
    philippines_tz = pytz.timezone('Asia/Manila')
    now_ph = datetime.now(philippines_tz)

    if not file or not reference_number or not amount or not payment_date_raw:
        flash("All fields are required.", "warning")
        return redirect(url_for('cx_dashboard', tab='upload'))

    # Use app.config directly here
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    try:
        payment_date = datetime.strptime(payment_date_raw, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format.", "danger")
        return redirect(url_for('cx_dashboard', tab='upload'))

    proof = PaymentProof(
        filename=filename,
        cx_id=current_user.id,
        reference_number=reference_number,
        payment_date=payment_date,
        amount=amount,
        uploaded_at=now_ph
    )

    db.session.add(proof)
    db.session.commit()
    flash("Proof of payment submitted successfully!", "success")
    return redirect(url_for('cx_dashboard', tab='billing', uploaded='true'))

@app.route('/cx/rebate', methods=['POST'])
@login_required
def rebate_request():
    req_type = request.form.get('type')
    billing_from = request.form.get('billing_from')
    billing_to = request.form.get('billing_to')
    soa_file = request.files.get('soa_file')
    rebate_amount = request.form.get('rebate_amount')
    overcharge_reason = request.form.get('overcharge_reason')

    if not soa_file:
        flash("SOA file is required.", "warning")
        return redirect(url_for('cx_dashboard', tab=req_type))

    # Use app.config directly here
    filepath_soa = os.path.join(app.config['SOA_FOLDER'], secure_filename(soa_file.filename)) # Save to SOA_FOLDER
    soa_file.save(filepath_soa)


    try:
        billing_from = datetime.strptime(billing_from, '%Y-%m-%d').date()
        billing_to = datetime.strptime(billing_to, '%Y-%m-%d').date()
    except ValueError:
        flash("Invalid billing cycle dates.", "danger")
        return redirect(url_for('cx_dashboard', tab=req_type))

    new_request = CxRequest(
        cx_id=current_user.id,
        type=req_type,
        reason=overcharge_reason if req_type == 'overcharge' else '',
        billing_from=billing_from,
        billing_to=billing_to,
        amount=float(rebate_amount) if rebate_amount else None,
        soa_filename=secure_filename(soa_file.filename) # Store just the filename
    )

    db.session.add(new_request)
    db.session.commit()
    flash(f"{req_type.title()} request submitted!", "success")
    return redirect(url_for('cx_dashboard', tab='billing'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Handle avatar upload
    avatar = request.files.get('avatar')
    if avatar and avatar.filename:
        filename = secure_filename(f"avatar_{current_user.id}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        avatar.save(filepath)
        current_user.avatar = filename

    # Update text fields
    current_user.name = request.form.get('name')
    current_user.email = request.form.get('email')
    current_user.contact = request.form.get('contact')
    current_user.first_name = request.form.get('first_name')
    current_user.middle_name = request.form.get('middle_name')
    current_user.surname = request.form.get('surname')
    current_user.gender = request.form.get('gender')
    current_user.location_country = request.form.get('location_country')
    current_user.location_region = request.form.get('location_region')
    current_user.location_province = request.form.get('location_province')
    current_user.location_city = request.form.get('location_city')
    current_user.location_barangay = request.form.get('location_barangay')
    current_user.location_zip = request.form.get('location_zip')
    current_user.location_street = request.form.get('location_street')

    # Convert birthdate string to datetime.date
    birthdate_str = request.form.get('birthdate')
    if birthdate_str:
        try:
            current_user.birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid birthdate format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for('cx_dashboard', tab='profile'))

    try:
        db.session.commit()
        flash("Profile updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating profile: {str(e)}", "danger")

    return redirect(url_for('cx_dashboard', tab='profile'))
    

@app.route('/cx/soa/view')
@login_required
def serve_soa_pdf():
    return redirect(url_for('static', filename='soa/soa_demo.pdf'))

@app.route('/cx/download_soa')
@login_required
def download_soa():
    return redirect(url_for('static', filename='soa/soa_demo.pdf'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('cx_login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # This creates tables based on models.py
    app.run(host='0.0.0.0', port=5000, debug=True)

@app.route('/test_flash')
def test_flash():
    flash("This is a test success message!", "success")
    return redirect(url_for('cx_dashboard', tab='profile'))