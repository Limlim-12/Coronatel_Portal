# app.py
# set FLASK_ENV=development 
# set FLASK_ENV=production

from flask import Flask, render_template, redirect, url_for, request, flash, get_flashed_messages, abort, session
from flask_mail import Mail
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, current_user # Removed LoginManager here
from datetime import datetime, date
from pytz import timezone
from functools import wraps
from extensions import db, login_manager, mail # Keep this import
from mailer import send_payment_status_email , send_request_status_email, send_account_verification_email # Make sure this is imported at the top
import pytz
import os
import random

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

philippines_tz = timezone('Asia/Manila')
now_ph = datetime.now(philippines_tz)

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
from models import Cx, PaymentProof, CxRequest, Notification, AdminUser, SOA, CxLoginLog, PrivateMessage, AdminMessage, ReactivationRequest, SupportTicket

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

        if user:
            if not user.is_verified:
                flash('Your account is not yet verified by admin. Please wait for confirmation.', 'warning')
                return render_template('cx/login.html', is_cx_login=True)

            if user.account_status == 'Inactive':
                flash('Your account has been deactivated by admin. Please contact support for assistance.', 'danger')
                return render_template('cx/login.html', is_cx_login=True)

            if user.account_status == 'TERMINATE':
                flash('Your account has been terminated and cannot be accessed.', 'danger')
                return render_template('cx/login.html', is_cx_login=True)

            if check_password_hash(user.password, password):
                session['user_type'] = 'cx'
                login_user(user)
                # Set account_status to ACTIVE on successful login
                if user.account_status != 'ACTIVE':
                    user.account_status = 'ACTIVE'
                    db.session.commit()
                flash('Logged in successfully!', 'success')

              
              
                login_entry = CxLoginLog(cx_id=user.id, timestamp=datetime.now(philippines_tz))
                db.session.add(login_entry)
                db.session.commit()

                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('cx_dashboard'))

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
            if existing_user.account_status == 'TERMINATE':
                flash('This email is associated with a terminated account and cannot be used.', 'danger')
                return render_template('cx/register.html')
            flash('Email already exists.', 'warning')
            return render_template('cx/register.html')

        # Check if account number already exists and is terminated
        existing_account = Cx.query.filter_by(account_number=account_number).first()
        if existing_account:
            if existing_account.account_status == 'TERMINATE':
                flash('This account number is associated with a terminated account and cannot be used.', 'danger')
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
    messages = AdminMessage.query.filter_by(cx_id=current_user.id).order_by(AdminMessage.sent_at.desc()).all()  # ✅ NEW

  # Load all notifications from the Notification table
    all_notifications = Notification.query.filter_by(cx_id=current_user.id).order_by(Notification.created_at.desc()).all()

    # Check if account is inactive and force logout
    if current_user.account_status == 'Inactive':
        flash('Your account has been deactivated by admin. Please contact support for assistance.', 'danger')
        logout_user()
        return redirect(url_for('cx_login'))

    # Check if account is terminated and force logout
    if current_user.account_status == 'TERMINATE':
        flash('Your account has been terminated and cannot be accessed.', 'danger')
        logout_user()
        return redirect(url_for('cx_login'))

    return render_template(
        'cx/dashboard.html',
        active_tab=tab,
        tab=tab,
        age=age,
        dashboard_header=True,
        previous_uploads=uploads,
        user_requests=requests,
        all_notifications=all_notifications,
        verified=verified,
        now=datetime.now(),
        previous_rebates=previous_rebates,             
        previous_overcharges=previous_overcharges,
        soa_files=soa_files,
        account_status=current_user.account_status,
        messages=messages  # ✅ Include admin messages  
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
        uploaded_at=datetime.now(timezone('Asia/Manila')),
        created_at=datetime.now(timezone('Asia/Manila')),
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
    if isinstance(current_user, Cx):
        current_user.account_status = 'INACTIVE'
        db.session.commit()
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('cx_login'))


from models import Cx, ReactivationRequest
from extensions import db
from flask import request, flash, redirect, url_for, render_template, abort
from flask_login import current_user, login_required
from datetime import datetime
import pytz

@app.route('/cx/account_termination_request', methods=['POST'])
def account_termination_request():
    email = request.form.get('email')
    reason = request.form.get('reason')

    if email and reason:
        cx = Cx.query.filter_by(email=email).first()
        if cx:
            new_request = ReactivationRequest(cx_id=cx.id, message=reason, status='PENDING', requested_at=datetime.now(pytz.timezone('Asia/Manila')))
            db.session.add(new_request)
            db.session.commit()
            flash('Your request has been submitted. Administrator will contact you soon.', 'success')
        else:
            flash('Email not found in our records.', 'warning')
    else:
        flash('Please fill out all fields.', 'warning')

    return redirect(url_for('cx_login'))

@app.route('/cx/support')
@login_required
def cx_support():
    return render_template('cx/support.html')





# ===== Routes for admin (These remain exactly as you had them, no change needed here from your previous app.py) =====
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')

        # Always use the fixed email and pick the most recently created admin
        admin = (
            AdminUser.query
            .filter_by(email='admin@coronatel.ph')
            .order_by(AdminUser.id.desc())
            .first()
        )

        if admin and admin.check_password(password):
            session['user_type'] = 'admin'
            login_user(admin)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    # reuse your CX login template, but switch to admin mode
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
        name       = request.form.get('name')
        password   = request.form.get('password')
        access_key = request.form.get('access_key')

        # Verify the access key
        if access_key != app.config['ADMIN_ACCESS_KEY']:
            flash('Invalid admin access key', 'error')
            return redirect(url_for('register_admin'))

        # Create new admin with fixed email
        new_admin = AdminUser(
            email='admin@coronatel.ph',
            name=name,
        )
        new_admin.set_password(password)

        try:
            db.session.add(new_admin)
            db.session.commit()
            flash('Admin account created successfully!', 'success')
            return redirect(url_for('admin_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating admin account: {e}', 'danger')

    return render_template('admin/register.html')




@app.route('/admin/dashboard/summary-data')
@login_required
def get_dashboard_summary_data():
    if not isinstance(current_user, AdminUser):
        abort(403)

    total_customers = Cx.query.count()
    active_requests = CxRequest.query.filter_by(status='PENDING').count()
    open_tickets = ReactivationRequest.query.filter_by(status='PENDING').count()
    recent_logins = CxLoginLog.query.filter(
        CxLoginLog.timestamp >= datetime.now().date()
    ).count()

    return {
        'total_customers': total_customers,
        'active_requests': active_requests,
        'open_tickets': open_tickets,
        'recent_logins': recent_logins
    }

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, AdminUser):
        abort(403)

    tab = request.args.get('tab', 'overview')
    inner_tab = request.args.get('inner_tab', 'payments')

    customers = Cx.query.all()
    manila_today = datetime.now(timezone('Asia/Manila')).date()

    context = {
        'active_tab': tab,
        'inner_tab': inner_tab,
        'customers': customers,
    }

    if tab == 'billing':
        context.update({
            'payment_proofs': PaymentProof.query.order_by(PaymentProof.uploaded_at.desc()).all(),
            'pending_proofs': PaymentProof.query.filter_by(status='PENDING').order_by(PaymentProof.uploaded_at.desc()).all(),
            'customer_requests': CxRequest.query.order_by(CxRequest.created_at.desc()).all(),
            'pending_requests': CxRequest.query.filter_by(status='PENDING').order_by(CxRequest.created_at.desc()).all(),
            'completed_requests_count': CxRequest.query.filter(CxRequest.status.in_(['APPROVED', 'REJECTED'])).count()
        })

    elif tab == 'overview':
        context.update({
            'recent_logins': CxLoginLog.query.order_by(CxLoginLog.timestamp.desc()).limit(3).all(),
            'login_count_today': CxLoginLog.query.filter(
                CxLoginLog.timestamp >= manila_today
            ).count(),
            'reactivation_requests': ReactivationRequest.query.filter_by(status='PENDING').order_by(ReactivationRequest.requested_at.desc()).all(),
            'pending_proofs': PaymentProof.query.filter_by(status='PENDING').order_by(PaymentProof.uploaded_at.desc()).all(),
            'pending_requests': CxRequest.query.filter_by(status='PENDING').order_by(CxRequest.created_at.desc()).all()
        })

    elif tab == 'accounts':
        return render_template('admin/account_tab.html', **context)

    elif tab == 'tickets':
        context.update({
            'support_tickets': SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
        })

    template_map = {
        'overview': 'admin/dashboard.html',
        'billing': 'admin/billing_tab.html',
        'accounts': 'admin/account_tab.html',
        'tickets': 'admin/support.html'  # ✅ Correct template
    }

    selected_template = template_map.get(tab, 'admin/dashboard.html')
    return render_template(selected_template, **context)




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
    # Send email
        send_payment_status_email(
        name=proof.cx.name,
        email=proof.cx.email,
        account_number=proof.cx.account_number,
        status=new_status,
        reference_number=proof.reference_number,
        payment_date=proof.payment_date,
        amount=proof.amount
    )

    # Create dashboard notification
    payment_date_str = proof.payment_date.strftime('%B %d, %Y') if proof.payment_date else 'N/A'
    message = (
        f"Your payment of ₱{proof.amount:.2f} made on {payment_date_str} "
        f"(Ref: {proof.reference_number}) has been {new_status}."
    )

    notif = Notification(
        cx_id=customer.id,
        notif_type='payment',
        status=new_status,
        amount=proof.amount,
        reference_id=proof.reference_number,
        message=message
    )
    db.session.add(notif)
    db.session.commit()




    flash(f'Payment marked as {new_status} and customer has been notified.', 'success')
    return redirect(url_for('admin_dashboard', tab='billing', inner_tab='payments'))




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

@app.route('/admin/delete_payment/<int:proof_id>', methods=['POST'])
@login_required
def admin_delete_payment(proof_id):
    proof = PaymentProof.query.get_or_404(proof_id)
    db.session.delete(proof)
    db.session.commit()
    flash('Payment proof deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='billing', inner_tab='payments'))

@app.route('/admin/delete_request/<int:req_id>', methods=['POST'])
@login_required
def admin_delete_request(req_id):
    req = CxRequest.query.get_or_404(req_id)
    db.session.delete(req)
    db.session.commit()
    flash('Request deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='billing', inner_tab='requests'))


@app.route('/admin/delete_soa/<int:soa_id>', methods=['POST'])
@login_required
def admin_delete_soa(soa_id):
    soa = SOA.query.get_or_404(soa_id)
    db.session.delete(soa)
    db.session.commit()
    flash('SOA deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='billing', inner_tab='soa-tab'))

@app.route('/cx/delete_admin_message/<int:msg_id>', methods=['POST'])
@login_required
def delete_admin_message(msg_id):
    msg = AdminMessage.query.get_or_404(msg_id)
    # Ensure the current user owns the message
    if msg.cx_id != current_user.id:
        abort(403)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted successfully.', 'success')
    return redirect(url_for('cx_dashboard'))



@app.route('/admin/update_request_status/<int:request_id>', methods=['POST'])
@login_required
def admin_update_request_status(request_id):
    req = CxRequest.query.get_or_404(request_id)
    new_status = request.form.get('new_status')

    if new_status in ['APPROVED', 'REJECTED']:
        req.status = new_status
        db.session.commit()

        # ✅ Email notification (only if email exists)
        if req.cx and req.cx.email:
            send_request_status_email(
                name=req.cx.name,
                email=req.cx.email,
                account_number=req.cx.account_number,
                req_type=req.type,
                status=new_status,
                billing_from=req.billing_from.strftime('%b %d, %Y') if req.billing_from else 'N/A',
                billing_to=req.billing_to.strftime('%b %d, %Y') if req.billing_to else 'N/A',
                amount=req.amount
            )

        # ✅ Safely build message with checks
        amount_str = f"₱{req.amount:.2f}" if req.amount is not None else "an unspecified amount"
        billing_range = ""
        if req.billing_from and req.billing_to:
            billing_range = f" ({req.billing_from.strftime('%b %d')}–{req.billing_to.strftime('%b %d')})"
        elif req.billing_from:
            billing_range = f" (from {req.billing_from.strftime('%b %d')})"
        elif req.billing_to:
            billing_range = f" (until {req.billing_to.strftime('%b %d')})"

        message = f"Your {req.type.lower()} request for {amount_str}{billing_range} has been {new_status}."

        # ✅ Create dashboard notification
        notif = Notification(
            cx_id=req.cx.id,
            notif_type=req.type.lower(),
            status=new_status,
            amount=req.amount,
            reference_id=str(req.id),
            message=message
        )
        db.session.add(notif)
        db.session.commit()

        flash(f'{req.type.capitalize()} request marked as {new_status} and customer notified.', 'success')
    else:
        flash('Invalid status update.', 'danger')

    return redirect(url_for('admin_dashboard', tab='billing'))



@app.route('/admin/upload_soa', methods=['POST'])
@login_required
def admin_upload_soa():
    account_number = request.form.get('account_number')
    billing_from = request.form.get('billing_from')
    billing_to = request.form.get('billing_to')
    soa_file = request.files.get('soa_file')

    # Check for file
    if not soa_file or soa_file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('admin_dashboard', tab='billing'))

    # Validate customer
    user = Cx.query.filter_by(account_number=account_number).first()
    if not user:
        flash('Account number not found.', 'danger')
        return redirect(url_for('admin_dashboard', tab='billing'))

    # Parse billing dates
    try:
        billing_from_date = datetime.strptime(billing_from, "%Y-%m-%d").date()
        billing_to_date = datetime.strptime(billing_to, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        flash('Invalid billing period. Please select valid dates.', 'danger')
        return redirect(url_for('admin_dashboard', tab='billing'))

    # Save file
    filename = secure_filename(soa_file.filename)
    save_path = os.path.join(app.config['SOA_FOLDER'], filename)
    soa_file.save(save_path)

    # Create new SOA record
    new_soa = SOA(
        cx_id=user.id,
        filename=filename,
        billing_from=billing_from_date,
        billing_to=billing_to_date
    )
    db.session.add(new_soa)
    db.session.commit()

    flash(f'SOA uploaded for {user.name or user.email}', 'success')
    return redirect(url_for('admin_dashboard', tab='billing'))


@app.route('/admin/manage_accounts')
@login_required
def manage_accounts():
    if not isinstance(current_user, AdminUser):
        abort(403)

    customers = Cx.query.order_by(Cx.created_at.desc()).all()  # if `created_at` exists, else just `.all()`
    return render_template('admin/manage_accounts.html', customers=customers)




@app.route('/admin/update_account_info/<int:cx_id>', methods=['POST'])
@login_required
def update_account_info(cx_id):
    if not isinstance(current_user, AdminUser):
        abort(403)

    from mailer import send_account_verification_email  # ✅ Import centralized mailer

    cx = Cx.query.get_or_404(cx_id)
    was_unverified = not cx.is_verified

    # Safely update only allowed fields
    cx.account_number = request.form.get('account_number') or cx.account_number
    cx.email = request.form.get('email') or cx.email
    cx.internet_status = request.form.get('internet_status') or cx.internet_status
    cx.internet_plan = request.form.get('internet_plan') or cx.internet_plan

    # ✅ Prevent overwriting account_status
    # ❌ cx.account_status = request.form.get('account_status')

    # ✅ Update is_verified safely
    is_verified_str = request.form.get('is_verified')
    if is_verified_str is not None:
        cx.is_verified = bool(int(is_verified_str))

    db.session.commit()

    if was_unverified and cx.is_verified:
        try:
            send_account_verification_email(cx.first_name or cx.name, cx.email, cx.account_number)
            flash('Account updated and email notification sent.', 'success')
        except Exception as e:
            flash(f'Account updated but failed to send email: {e}', 'warning')
    else:
        flash(f"Updated account for {cx.email}", 'success')

    return redirect(url_for('admin_dashboard', tab='users'))



@app.route('/admin/delete_account/<int:cx_id>', methods=['POST'])
@login_required
def delete_account(cx_id):
    if not isinstance(current_user, AdminUser):
        abort(403)

    cx = Cx.query.get_or_404(cx_id)
    cx.account_status = 'TERMINATE'  # Use consistent TERMINATE label
    db.session.commit()
    flash(f"Account for {cx.name} has been terminated.", "success")
    return redirect(url_for('admin_dashboard', tab='users'))

@app.route('/admin/restore_account/<int:cx_id>', methods=['POST'])
@login_required
def restore_account(cx_id):
    if not isinstance(current_user, AdminUser):
        abort(403)

    cx = Cx.query.get_or_404(cx_id)
    cx.account_status = 'ACTIVE'

    # Approve the latest pending reactivation request (if any)
    reactivation_request = ReactivationRequest.query.filter_by(cx_id=cx_id, status='PENDING').first()
    if reactivation_request:
        reactivation_request.status = 'APPROVED'
        reactivation_request.resolved_at = datetime.now()

    db.session.commit()
    flash(f"Account for {cx.name} has been reactivated.", "success")
    return redirect(url_for('admin_dashboard', tab='overview'))





@app.route('/admin/send_message/<int:cx_id>', methods=['POST'])
@login_required
def send_admin_message(cx_id):
    if not isinstance(current_user, AdminUser):
        abort(403)

    from models import Cx  # Fix: import Cx model here

    cx = Cx.query.get_or_404(cx_id)

    message = request.form.get('message', '').strip()
    if message:
        new_msg = AdminMessage(
            cx_id=cx.id,
            sender_id=current_user.id,
            subject='Admin Message',
            body=message,
            sent_at=datetime.now(timezone('Asia/Manila'))
        )
        db.session.add(new_msg)
        db.session.commit()
        flash(f'Message sent to {cx.name}.', 'success')
    else:
        flash('Message cannot be empty.', 'warning')

    return redirect(url_for('admin_dashboard', tab='users'))


@app.route('/request-reactivation', methods=['POST'])
def request_reactivation():
    cx_id = request.form.get('cx_id')
    email = request.form.get('email').strip().lower()
    message = request.form.get('message')

    # Validate required fields
    if not email or not message:
        flash('All fields are required to request reactivation.', 'danger')
        return redirect(url_for('cx_login'))

    # 🛡 Fallback: If cx_id is missing, try to get customer by email
    if not cx_id:
        customer = Cx.query.filter_by(email=email).first()
        if not customer:
            flash('No customer found with that email address.', 'danger')
            return redirect(url_for('cx_login'))
        cx_id = customer.id
    else:
        customer = Cx.query.get(cx_id)
        if not customer:
            flash('Invalid customer account.', 'danger')
            return redirect(url_for('cx_login'))

    # 🔒 Prevent duplicate reactivation request by email
    existing_email_request = ReactivationRequest.query.filter_by(email=email, status='PENDING').first()
    if existing_email_request:
        flash('A pending reactivation request already exists for this email.', 'warning')
        return redirect(url_for('cx_login'))

    # 🔒 Optional: Prevent duplicate by cx_id
    existing_cx_request = ReactivationRequest.query.filter_by(cx_id=cx_id, status='PENDING').first()
    if existing_cx_request:
        flash('You already have a pending reactivation request.', 'warning')
        return redirect(url_for('cx_login'))

    # ✅ Save new request
    new_request = ReactivationRequest(
        cx_id=cx_id,
        email=email,
        message=message,
        status='PENDING',
        requested_at=datetime.now(pytz.timezone('Asia/Manila'))
    )
    db.session.add(new_request)
    db.session.commit()

    flash('Your request for reactivation has been submitted.', 'success')
    return redirect(url_for('cx_login'))



def generate_ticket_number():
    from random import randint
    return f"CT-{randint(100, 999)}-{randint(100, 999)}"


@app.route('/submit-support', methods=['POST'])
@login_required
def submit_support():
    from random import randint

    def generate_ticket_number():
        return f"CT-{randint(100, 999)}-{randint(100, 999)}"

    ticket_number = generate_ticket_number()

    # Determine ticket type based on form input
    raw_form_type = request.form.get('form_type')
    ticket_type = 'repair' if raw_form_type == 'repair' else 'account' if raw_form_type == 'account' else None

    if not ticket_type:
        flash("Please select a valid ticket type.", "danger")
        return redirect(url_for('cx_support'))

    # Common fields
    account_type = request.form.get('account_type')
    contact_person = request.form.get('contact_person')
    contact_number = request.form.get('contact_number')
    service_address = request.form.get('service_address')

    # Repair-specific fields
    issue_type = request.form.get('issue_type') if ticket_type == 'repair' else None
    other_issue_detail = request.form.get('other_issue_detail') if ticket_type == 'repair' and issue_type == 'Others' else None
    request_service = request.form.get('request_service') if ticket_type == 'repair' else None
    repair_note = request.form.get('repair_note') if ticket_type == 'repair' else None

    # Account-specific fields
    account_request = request.form.get('account_request') if ticket_type == 'account' else None
    new_plan = request.form.get('new_plan') if ticket_type == 'account' and account_request == 'Change Internet Plan' else None
    account_note = request.form.get('account_note') if ticket_type == 'account' else None

    # Create the SupportTicket object
    ticket = SupportTicket(
        ticket_number=ticket_number,
        cx_id=current_user.id,
        ticket_type=ticket_type,
        account_type=account_type,
        contact_person=contact_person,
        contact_number=contact_number,
        service_address=service_address,
        issue_type=issue_type,
        other_issue_detail=other_issue_detail,
        request_service=request_service,
        repair_note=repair_note,
        account_request=account_request,
        new_plan=new_plan,
        account_note=account_note
    )

    db.session.add(ticket)
    db.session.commit()

    # Debug: flash ticket id after commit
    # flash(f"Debug: Ticket created with ID {ticket.id}", "info")

    flash(f"Support ticket submitted! Ticket No: {ticket_number}", "success")
    return redirect(url_for('cx_support'))



def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_authenticated and getattr(current_user, 'email', None) == 'admin@coronatel.ph'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/support')
@login_required
@admin_required
def admin_support():
    status = request.args.get('status')
    detail_id = request.args.get('detail_id', type=int)

    # Fetch ticket list
    if status:
        tickets = SupportTicket.query.filter_by(status=status).order_by(SupportTicket.created_at.desc()).all()
    else:
        tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()

    # Load selected ticket for popup detail view
    ticket_detail = None
    if detail_id:
        ticket_detail = SupportTicket.query.get(detail_id)
        if ticket_detail:
            # force load cx if not already loaded
            _ = ticket_detail.cx  

    return render_template('admin/support.html', tickets=tickets, ticket_detail=ticket_detail)



@app.route('/admin/support/<int:ticket_id>')
@login_required
@admin_required
def view_ticket_detail(ticket_id):
    # Since the user wants to integrate ticket detail inside admin/support.html,
    # redirect to admin_support with detail_id query param instead of separate template
    return redirect(url_for('admin_support', detail_id=ticket_id))






@app.route('/admin/support/<int:ticket_id>/status', methods=['POST'])
@login_required
@admin_required
def update_ticket_status(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    ticket.status = request.form['status']
    db.session.commit()
    return redirect(url_for('admin_support'))

@app.route('/admin/support/delete/<int:ticket_id>', methods=['POST'])
@login_required
@admin_required
def delete_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash(f'Ticket #{ticket.ticket_number} has been successfully deleted.', 'success')
    return redirect(url_for('admin_support'))

@app.route('/admin/support/bulk-delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_tickets():
    ticket_ids = request.form.getlist('ticket_ids[]')  # Get selected IDs
    if not ticket_ids:
        flash('No tickets selected for deletion.', 'info')
        return redirect(url_for('admin_support'))

    deleted_count = 0
    for tid in ticket_ids:
        ticket = SupportTicket.query.get(tid)
        if ticket:
            db.session.delete(ticket)
            deleted_count += 1

    db.session.commit()
    flash(f'{deleted_count} support ticket(s) deleted.', 'success')
    return redirect(url_for('admin_support'))



@app.route('/admin/support/assign/<int:ticket_id>', methods=['POST'])
@login_required
def assign_admin_ticket(ticket_id):
    # Example logic:
    if current_user.role != 'admin':
        abort(403)
    ticket = SupportTicket.query.get_or_404(ticket_id)
    # You could add a field like `assigned_admin_id = db.Column(...)` and set it here
    flash(f"Ticket #{ticket.ticket_number} assigned to you.", "info")
    return redirect(url_for('admin_support'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all() # This creates tables based on models.py
    app.run(host='0.0.0.0', port=5000, debug=True)



