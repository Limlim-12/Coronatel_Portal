# patch_status.py

from app import app, db  # adjust if your app is not named app.py
from models import PaymentProof  # or from app.models if needed

with app.app_context():
    proofs = PaymentProof.query.filter(PaymentProof.status == None).all()
    for p in proofs:
        p.status = 'PENDING'
    db.session.commit()
    print(f"Updated {len(proofs)} records to 'PENDING'")
