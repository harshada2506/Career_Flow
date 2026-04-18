import smtplib
from email.mime.text import MIMEText

# Replace with your Gmail + Gmail App Password (NOT normal password)
GMAIL_USER = "sunitabhogade333@gmail.com"
GMAIL_APP_PASSWORD = "ejvf rqkn zhbj xxkt"

def send_otp_email(to_email: str, otp: str):
    body = f"Your CareerFlow OTP is: {otp}\n\nThis OTP is valid for 5 minutes."
    msg = MIMEText(body)
    msg["Subject"] = "CareerFlow OTP Verification"
    msg["From"] = GMAIL_USER
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)