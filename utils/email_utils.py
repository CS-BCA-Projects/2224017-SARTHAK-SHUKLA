from flask_mail import Message
from extensions import mail

def send_email(subject, recipient, body):
    try:
        print(f"📧 Attempting to send email to {recipient}...")
        msg = Message(subject=subject, sender="your-email@gmail.com", recipients=[recipient])
        msg.body = body
        mail.send(msg)
        print(f"✅ Email successfully sent to {recipient}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
