from werkzeug.security import generate_password_hash
from app import app
from extensions import db
from models import Cx

with app.app_context():
    existing_admin = Cx.query.filter_by(email='admin@coronatel').first()
    if existing_admin:
        print("Admin already exists.")
    else:
        admin = Cx(
            email='admin@coronatel',
            password=generate_password_hash('admin123'),  # You can change this password
            name='System Admin',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully.")
