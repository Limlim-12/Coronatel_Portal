# ✅ Final corrected models.py with consistent 'cx' relationship

from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pytz import timezone

def now_manila():
    return datetime.now(timezone('Asia/Manila'))

# --- Customer Model ---
class Cx(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(120))
    avatar = db.Column(db.String(255), default='default.png')
    role = db.Column(db.String(10), nullable=False, default='customer')

    account_status = db.Column(db.String(20), default='Active')

    # Account details
    contact = db.Column(db.String(50))
    account_number = db.Column(db.String(50))
    internet_plan = db.Column(db.String(50))
    is_verified = db.Column(db.Boolean, default=False)  # ✅ NEW

    # Personal info
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    middle_initial = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    extension_name = db.Column(db.String(50))
    birthdate = db.Column(db.Date)
    gender = db.Column(db.String(20))

    # Address
    location_country = db.Column(db.String(50))
    location_region = db.Column(db.String(50))
    location_province = db.Column(db.String(50))
    location_city = db.Column(db.String(50))
    location_barangay = db.Column(db.String(50))
    location_zip = db.Column(db.String(20))
    location_street = db.Column(db.String(100))

    # Relationships
    payment_proofs = db.relationship('PaymentProof', back_populates='cx', lazy=True)
    requests = db.relationship('CxRequest', back_populates='cx', lazy=True)
    soa_files = db.relationship('SOA', back_populates='cx', lazy=True)
    notifications = db.relationship('Notification', back_populates='cx', lazy=True)
    login_logs = db.relationship('CxLoginLog', back_populates='cx', lazy=True)

    def __repr__(self):
        return f"<Cx {self.email}>"

# --- PaymentProof ---
class PaymentProof(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'))
    uploaded_at = db.Column(db.DateTime, default=now_manila)
    reference_number = db.Column(db.String(100))
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='PENDING')

    cx = db.relationship('Cx', back_populates='payment_proofs')

    def __repr__(self):
        return f"<PaymentProof {self.reference_number} | Cx_ID: {self.cx_id}>"

# --- CxRequest ---
class CxRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'))
    type = db.Column(db.String(50))
    reason = db.Column(db.Text)
    billing_from = db.Column(db.Date)
    billing_to = db.Column(db.Date)
    amount = db.Column(db.Float)
    soa_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now_manila)
    uploaded_at = db.Column(db.DateTime, default=now_manila)
    status = db.Column(db.String(20), default='PENDING')
    admin_note = db.Column(db.Text)
    response_note = db.Column(db.Text)

    cx = db.relationship('Cx', back_populates='requests')

    def __repr__(self):
        return f"<CxRequest {self.type} | Cx_ID: {self.cx_id}>"

# --- SOA ---
class SOA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'), nullable=False)
    filename = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=now_manila)
    billing_from = db.Column(db.Date)
    billing_to = db.Column(db.Date)

    cx = db.relationship('Cx', back_populates='soa_files')

    def __repr__(self):
        return f"<SOA Cx_ID: {self.cx_id} | {self.filename}>"

# --- Notification ---
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=now_manila)
    notif_type = db.Column(db.String(50))
    status = db.Column(db.String(50))
    amount = db.Column(db.Float)
    reference_id = db.Column(db.String(100))

    cx = db.relationship('Cx', back_populates='notifications')

    def __repr__(self):
        return f"<Notification cx_id={self.cx_id}, type={self.notif_type}, status={self.status}>"

# --- CxLoginLog ---
class CxLoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=now_manila)

    cx = db.relationship('Cx', back_populates='login_logs')

    def __repr__(self):
        return f"<CxLoginLog cx_id={self.cx_id}, time={self.timestamp}>"

# --- AdminUser ---
class AdminUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(255))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# --- PrivateMessage ---
class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('cx.id'), nullable=False)
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=now_manila)
    is_read = db.Column(db.Boolean, default=False)

    sender = db.relationship('AdminUser', backref='sent_messages')
    recipient = db.relationship('Cx', backref='received_messages')

    def __repr__(self):
        return f"<PrivateMessage from Admin {self.sender_id} to CX {self.recipient_id}>"


# --- AdminMessage (Global Update Notices) ---
class AdminMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('admin_user.id'), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=now_manila)

    cx = db.relationship('Cx', backref='admin_messages')
    sender = db.relationship('AdminUser', backref='broadcasts')

    def __repr__(self):
        return f"<AdminMessage to {self.cx_id}: {self.subject}>"

class ReactivationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(100), db.ForeignKey('cx.account_number'))
    email = db.Column(db.String(150), unique=True)
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='PENDING')  # Options: PENDING, APPROVED, REJECTED
    requested_at = db.Column(db.DateTime, default=now_manila)

    cx = db.relationship('Cx', backref='reactivation_requests', foreign_keys=[cx_id])


class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)

    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'), nullable=False)

    # ✅ Proper relationship to Cx model for Jinja2 usage
    cx = db.relationship('Cx', backref=db.backref('support_tickets', lazy=True))

    # Ticket type: 'repair' or 'account'
    ticket_type = db.Column(db.String(50))

    # Common info
    account_type = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    contact_number = db.Column(db.String(50))
    service_address = db.Column(db.String(255))

    # For Repair tickets
    issue_type = db.Column(db.String(100))
    other_issue_detail = db.Column(db.String(255))  # If issue_type == 'Others'
    request_service = db.Column(db.String(100))
    repair_note = db.Column(db.Text)

    # For Account Management tickets
    account_request = db.Column(db.String(100))
    new_plan = db.Column(db.String(100))  # If account_request == 'Change Internet Plan'
    account_note = db.Column(db.Text)

    # Status tracking
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=now_manila)
