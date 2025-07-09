# mailer.py

from flask_mail import Message
from flask import current_app
from extensions import mail  # Change 'app' to the actual module where 'mail' is initialized

def send_payment_status_email(name, email, account_number, status, reference_number, payment_date, amount):
    subject = f"[Corona Telecom] Payment {status}"

    if status == 'VERIFIED':
        body = f"""
Hi {name},

Good day!

Thank you for your payment. We’re writing to confirm that we have successfully verified your recent payment with the following details:

Transaction Reference Number: {reference_number}

Transaction Date: {payment_date}

Amount: Php {amount}

Account Number: {account_number}

Your account has been updated accordingly.

Should you require a copy of your updated Statement of Account or an official receipt for your records, please let us know, and we’ll be glad to provide it.

If you have any further questions or need additional assistance, feel free to reply to this email.

Best regards,
Billing Team
billing@coronatel.com
"""
        

    elif status == 'REJECTED':
        body = f"""
Hi {name},

Good day.

Thank you for sending your proof of payment. After careful verification, we were unable to match this transaction to your account.

To help us validate your payment, could you please provide any of the following:

A clearer copy of the payment receipt or deposit slip

Confirmation of the transaction reference number

The exact date and time the payment was made

The name of the bank or channel used for the payment

Once we receive these details, we will reprocess the verification promptly.

We apologize for any inconvenience this may cause and appreciate your understanding and cooperation.

If you have any questions, please feel free to reply to this email.

Best regards,
Billing Team
billing@coronatel.com
"""
    else:
        return  # Do not send email for other statuses

    # Use Flask-Mail to send
    msg = Message(subject=subject, recipients=[email], body=body)
    mail.send(msg)
