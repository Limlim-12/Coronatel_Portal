# models.py

from extensions import db
from flask_login import UserMixin
from datetime import datetime

# Customer/User model
class Cx(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hashed password
    name = db.Column(db.String(120))
    avatar = db.Column(db.String(255), default='default.png')

    # Account details
    contact = db.Column(db.String(50))
    account_number = db.Column(db.String(50))
    internet_plan = db.Column(db.String(50))

    # Personal information
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    middle_initial = db.Column(db.String(50)) # Kept this for historical reasons or if you plan to use it differently
    surname = db.Column(db.String(50))
    extension_name = db.Column(db.String(50)) # Added this column
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
    payments = db.relationship('PaymentProof', backref='customer', lazy=True)
    requests = db.relationship('CxRequest', backref='customer', lazy=True)

    def __repr__(self):
        return f"<Cx {self.email}>"


# Payment proof model
class PaymentProof(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference_number = db.Column(db.String(100))
    payment_date = db.Column(db.Date)
    amount = db.Column(db.Float)

    def __repr__(self):
        return f"<PaymentProof {self.reference_number} | Cx_ID: {self.cx_id}>"


# Request (Rebate / Overcharge) model
class CxRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cx_id = db.Column(db.Integer, db.ForeignKey('cx.id'))
    type = db.Column(db.String(50))  # rebate / overcharge
    reason = db.Column(db.Text)
    billing_from = db.Column(db.Date)
    billing_to = db.Column(db.Date)
    amount = db.Column(db.Float)
    soa_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CxRequest {self.type} | Cx_ID: {self.cx_id}>"