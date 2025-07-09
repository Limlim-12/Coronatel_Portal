# app.py
# set FLASK_ENV=development 
# set FLASK_ENV=production

from flask import Flask, render_template, redirect, url_for, request, flash, get_flashed_messages, abort, session
from flask_mail import Mail
from mailer import send_payment_status_email  # If your file is named `email.py`
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user # Removed LoginManager here
from datetime import datetime, date
from extensions import db, login_manager, mail # Keep this import
import pytz
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_ACCESS_KEY'] = 'admin123coronatel'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SOA_FOLDER'] = 'static/soa'
app.config['ENV_MODE'] = os.getenv('FLASK_ENV', 'development')

# Example Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lim.coronatel@gmail.com'
app.config['MAIL_PASSWORD'] = 'ttxjsetcjlddstss'  # Use Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = ('Corona Telecom', 'lim.coronatel@gmail.com')

mail = Mail(app)

app.secret_key = 'admin123coronatel'  # already done if using app.config['SECRET_KEY']
login_manager.init_app(app)
login_manager.login_view = 'admin_login'  # IMPORTANT


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
from models import Cx, PaymentProof, CxRequest, Notification, AdminUser, SOA

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Cx, int(user_id))


# ===== Routes for cx (These remain exactly as you had them, no change needed here from your previous app.py) =====
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
            session['user_type'] = 'cx'
            login_user(user)
            flash('Logged in successfully!', 'success')

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('cx_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            return render_template('cx/login.html', is_cx_login=True)

    return render_template('cx/login.html', is_cx_login=True)





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
    verified = request.args.get('verified') 
    age = calculate_age(current_user.birthdate) if hasattr(current_user, 'birthdate') else None


    # Load data
    uploads = PaymentProof.query.filter_by(cx_id=current_user.id).order_by(PaymentProof.uploaded_at.desc()).all()
    requests = CxRequest.query.filter_by(cx_id=current_user.id).order_by(CxRequest.uploaded_at.desc()).all()
    previous_rebates = [r for r in requests if r.type == 'rebate']
    previous_overcharges = [r for r in requests if r.type == 'overcharge']
    soa_files = SOA.query.filter_by(cx_id=current_user.id).order_by(SOA.uploaded_at.desc()).all()


    # Build payment notifications
    payment_notifications = []
    for proof in uploads:
        if proof.status == 'VERIFIED':
            msg = f"✅ Your payment from {proof.payment_date.strftime('%b %d')} was marked as VERIFIED."
        elif proof.status == 'REJECTED':
            msg = f"❌ Your payment from {proof.payment_date.strftime('%b %d')} was REJECTED. Please re-upload."
        elif proof.status == 'PENDING':
            msg = f"⏳ Your payment from {proof.payment_date.strftime('%b %d')} is still pending verification."
        else:
            msg = f"ℹ️ Your payment from {proof.payment_date.strftime('%b %d')} has status: {proof.status}."

        payment_notifications.append({
            'id': proof.id,
            'date': proof.payment_date.strftime('%b %d, %Y'),
            'amount': proof.amount,
            'status': proof.status,
            'message': msg
        })

    return render_template(
        'cx/dashboard.html',
        active_tab=tab,
        tab=tab,
        age=age,
        dashboard_header=True,
        previous_uploads=uploads,
        user_requests=requests,
        payment_notifications=payment_notifications,
        verified=verified,
        now=datetime.now(),
        previous_rebates=previous_rebates,             
        previous_overcharges=previous_overcharges,
        soa_files=soa_files     
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
    req_type = request.form.get('type')  # 'rebate' or 'overcharge'
    billing_from = request.form.get('billing_from')
    billing_to = request.form.get('billing_to')
    soa_file = request.files.get('soa_file')
    rebate_amount = request.form.get('rebate_amount')
    overcharge_reason = request.form.get('overcharge_reason')
    request_id = request.form.get('request_id')
    response_note = request.form.get('response_note')

    # Handle response to admin note
    if request_id and response_note:
        req = CxRequest.query.get(int(request_id))
        if req and req.cx_id == current_user.id:
            req.response_note = response_note
            req.status = 'PENDING'
            db.session.commit()
            flash("Your response has been submitted.", "success")
        else:
            flash("Invalid request ID.", "danger")
        return redirect(url_for('cx_dashboard', tab='billing'))

    # Handle new request (rebate or overcharge)
    if not soa_file:
        flash("SOA file is required.", "warning")
        return redirect(url_for('cx_dashboard', tab='billing'))

    filename = secure_filename(soa_file.filename)
    filepath = os.path.join(app.config['SOA_FOLDER'], filename)
    soa_file.save(filepath)

    try:
        billing_from = datetime.strptime(billing_from, '%Y-%m-%d').date()
        billing_to = datetime.strptime(billing_to, '%Y-%m-%d').date()
    except ValueError:
        flash("Invalid billing cycle dates.", "danger")
        return redirect(url_for('cx_dashboard', tab='billing'))

    new_request = CxRequest(
        cx_id=current_user.id,
        type=req_type,
        reason=overcharge_reason if req_type == 'overcharge' else '',
        billing_from=billing_from,
        billing_to=billing_to,
        amount=float(rebate_amount) if rebate_amount else None,
        soa_filename=filename,
        uploaded_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        status='PENDING'
    )

    db.session.add(new_request)
    db.session.commit()

    flash(f"{req_type.title()} request submitted successfully!", "success")
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
    latest_soa = SOA.query.filter_by(cx_id=current_user.id).order_by(SOA.uploaded_at.desc()).first()
    if latest_soa:
        return redirect(url_for('static', filename='soa/' + latest_soa.filename))
    else:
        flash("No SOA available for viewing.", "warning")
        return redirect(url_for('cx_dashboard', tab='soa'))


@app.route('/cx/download_soa')
@login_required
def download_soa():
    latest_soa = SOA.query.filter_by(cx_id=current_user.id).order_by(SOA.uploaded_at.desc()).first()
    if latest_soa:
        return redirect(url_for('static', filename='soa/' + latest_soa.filename))
    else:
        flash("No SOA available for download.", "warning")
        return redirect(url_for('cx_dashboard', tab='soa'))







@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('cx_login'))



# ===== Routes for admin (These remain exactly as you had them, no change needed here from your previous app.py) =====
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admin = AdminUser.query.filter_by(email=email).first()

        if admin and admin.check_password(password):
            session['user_type'] = 'admin'
            login_user(admin)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('cx/login.html', is_admin_login=True)







@login_manager.user_loader
def load_user(user_id):
    user_type = session.get('user_type')

    if user_type == 'admin':
        return AdminUser.query.get(int(user_id))
    else:
        return Cx.query.get(int(user_id))  # Cx model for customers






@app.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        access_key = request.form.get('access_key')

        # Check access key
        if access_key != app.config['ADMIN_ACCESS_KEY']:
            flash('Invalid admin access key', 'error')
            return redirect(url_for('register_admin'))

        # Check if password already used
        existing_admins = AdminUser.query.filter_by(email='admin@coronatel.ph').all()
        for admin in existing_admins:
            if admin.check_password(password):
                flash('Password already used by another admin', 'error')
                return redirect(url_for('register_admin'))

        # Create new admin
        new_admin = AdminUser(email='admin@coronatel.ph', name=name)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()

        flash('Admin account created successfully!', 'success')
        return redirect(url_for('cx_login'))

    return render_template('admin/register.html')






@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, AdminUser):
        abort(403)

    tab = request.args.get('tab', 'overview')

    customers = Cx.query.all()
    payment_proofs = PaymentProof.query.order_by(PaymentProof.uploaded_at.desc()).all()
    customer_requests = CxRequest.query.order_by(CxRequest.created_at.desc()).all()

    # 🧠 Dynamically choose the correct template
    template = 'admin/billing_tab.html' if tab == 'billing' else 'admin/dashboard.html'

    return render_template(
        template,
        active_tab=tab,
        customers=customers,
        payment_proofs=payment_proofs,
        customer_requests=customer_requests
    )



@app.route('/admin/update_payment_status/<int:proof_id>', methods=['POST'])
@login_required
def admin_update_payment_status(proof_id):
    proof = PaymentProof.query.get_or_404(proof_id)
    new_status = request.form.get('status')

    if new_status not in ['VERIFIED', 'REJECTED', 'PENDING']:
        flash('Invalid status update.', 'danger')
        return redirect(url_for('admin_dashboard', tab='billing'))

    proof.status = new_status
    db.session.commit()

    customer = proof.cx
    if customer and customer.email and new_status in ['VERIFIED', 'REJECTED']:
        send_payment_status_email(
            name=proof.cx.name,
            email=proof.cx.email,
            account_number=proof.cx.account_number,
            status=new_status,
            reference_number=proof.reference_number,
            payment_date=proof.payment_date,
            amount=proof.amount
)


    flash(f'Payment marked as {new_status} and customer has been notified.', 'success')
    return redirect(url_for('admin_dashboard', tab='billing'))




@app.route('/delete_notification/<int:note_id>', methods=['POST'])
@login_required
def delete_notification(note_id):
    note = Notification.query.get_or_404(note_id)

    # Make sure the logged-in user owns this notification
    if note.cx_id != current_user.id:
        abort(403)

    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('cx_dashboard'))




@app.route('/admin/update_request_status/<int:request_id>', methods=['POST'])
@login_required
def admin_update_request_status(request_id):
    req = CxRequest.query.get_or_404(request_id)
    new_status = request.form.get('new_status')
    if new_status in ['APPROVED', 'REJECTED']:
        req.status = new_status
        db.session.commit()
        flash(f'Request status updated to {new_status}.', 'success')
    return redirect(url_for('admin_dashboard', tab='billing'))


@app.route('/admin/upload_soa', methods=['POST'])
@login_required
def admin_upload_soa():
    account_number = request.form.get('account_number')
    soa_file = request.files.get('soa_file')

    if not soa_file or soa_file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('admin_dashboard', tab='billing'))

    user = Cx.query.filter_by(account_number=account_number).first()
    if not user:
        flash('Account number not found.', 'danger')
        return redirect(url_for('admin_dashboard', tab='billing'))

    filename = secure_filename(soa_file.filename)
    save_path = os.path.join(app.config['SOA_FOLDER'], filename)
    soa_file.save(save_path)

    new_soa = SOA(cx_id=user.id, filename=filename)
    db.session.add(new_soa)
    db.session.commit()

    flash(f'SOA uploaded for {user.name or user.email}', 'success')
    return redirect(url_for('admin_dashboard', tab='billing'))





if __name__ == '__main__':
    with app.app_context():
        db.create_all() # This creates tables based on models.py
    app.run(host='0.0.0.0', port=5000, debug=True)



