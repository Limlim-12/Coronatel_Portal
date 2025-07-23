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

Thank you for your payment. We have successfully verified your recent payment with the following details:

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



def send_request_status_email(name, email, account_number, req_type, status, billing_from, billing_to, amount):
    req_type_clean = req_type.capitalize()
    subject = f"[Corona Telecom] {req_type_clean} Request {status}"

    if status == 'APPROVED':
        body = f"""
Hi {name},

Good day!

We are pleased to inform you that your recent {req_type} request has been approved.

Here are the details of your request:

Request Type: {req_type_clean}  
Billing Period: {billing_from} to {billing_to}  
Approved Amount: Php {amount}  
Account Number: {account_number}

The approved amount will be reflected in your upcoming billing cycle.

Should you have any questions or require further assistance, feel free to reply to this email.

Thank you for being a valued customer of Corona Telecom.

Best regards,  
Billing Team  
billing@coronatel.com
"""
    elif status == 'REJECTED':
        body = f"""
Hi {name},

Good day.

We’re writing to inform you that after reviewing your recent {req_type} request, we are unable to approve it at this time.

Here are the request details:

Request Type: {req_type_clean}  
Billing Period: {billing_from} to {billing_to}  
Requested Amount: Php {amount}  
Account Number: {account_number}

If you believe this decision was made in error or you have more documents or clarification to provide, please feel free to reply to this email so we may reevaluate your request.

We appreciate your understanding.

Best regards,  
Billing Team  
billing@coronatel.com
"""
    else:
        return  # Only send email for APPROVED or REJECTED

    msg = Message(subject=subject, recipients=[email], body=body)
    mail.send(msg)
    subject = f"[Corona Telecom] Your {req_type.capitalize()} Request was {status.capitalize()}"
    status_icon = "✅" if status.upper() == "APPROVED" else "❌"

    html = f"""
    <h3>{status_icon} Hello, {name}!</h3>
    <p>This is to inform you that your <strong>{req_type}</strong> request has been <strong>{status}</strong>.</p>
    <ul>
        <li><strong>Account No:</strong> {account_number}</li>
        <li><strong>Billing Period:</strong> {billing_from} to {billing_to}</li>
        <li><strong>Amount:</strong> ₱{amount}</li>
    </ul>
    <p>If you have further concerns, feel free to reply to this email or reach out to customer support.</p>
    <br>
    <p>Thank you for choosing Corona Telecom.</p>
    """

    msg = Message(subject, recipients=[email], html=html)
    mail.send(msg)




def send_account_verification_email(name, email, account_number):
    subject = "[Corona Telecom] Your Account is Now Verified"
    body = f"""Hi {name},

Good news!

Your Corona Telecom account has been verified. You can now log in to the customer portal using your registered credentials.

Verified Account Number: {account_number}

Thank you for choosing Corona Telecom.

Best regards,  
Support Team  
billing@coronatel.com
"""
    msg = Message(subject=subject, recipients=[email], body=body)
    mail.send(msg)


def send_account_termination_email(name, email, account_number):
    subject = "[Corona Telecom] Account Termination Notice"

    body = f"""Hi {name},

We regret to inform you that your Corona Telecom account has been terminated as of today.

Account Number: {account_number}

If you believe this was a mistake or you wish to discuss this matter further, please reach out to us immediately.

We appreciate your past patronage and are here to assist should you decide to reactivate your services in the future.

Best regards,  
Account Management Team  
billing@coronatel.com
"""

    msg = Message(subject=subject, recipients=[email], body=body)
    mail.send(msg)


def send_account_reactivation_email(name, email, account_number):
    subject = "[Corona Telecom] Account Reactivated Successfully"

    body = f"""Hi {name},

Good news!

Your Corona Telecom account has been reactivated. You may now resume access to your services and customer portal.

Account Number: {account_number}

If you encounter any issues or have questions regarding your account status, please don’t hesitate to contact us.

Thank you for staying with Corona Telecom.

Best regards,  
Account Management Team  
billing@coronatel.com
"""

    msg = Message(subject=subject, recipients=[email], body=body)
    mail.send(msg)
