import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import dotenv as _dotenv

_dotenv.load_dotenv()

GMAIL_ID = os.environ['GMAIL_ID']
GMAIL_PASS = os.environ['GMAIL_PASS']
RECIEVER_ADD = os.environ['RECIEVER_ADD']

def sendEmail(freezer_id, freezer_name):
    smtp_user = GMAIL_ID
    smtp_password = GMAIL_PASS
    server = 'smtp.gmail.com'
    port = 587
    msg = MIMEMultipart("alternative")
    msg["Subject"] = 'Freezer Alarm'
    msg["From"] = GMAIL_ID
    msg["To"] = RECIEVER_ADD
    msg.attach(MIMEText(f"""\n
    Freezer is overheating
    Freezer ID : {freezer_id}
    Freezer Name : {freezer_name}
    """, 'plain'))
    s = smtplib.SMTP(server, port)
    s.ehlo()
    s.starttls()
    s.login(smtp_user, smtp_password)
    s.sendmail(smtp_user, RECIEVER_ADD, msg.as_string())
    s.quit()
