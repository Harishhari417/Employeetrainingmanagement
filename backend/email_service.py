import os
import base64
import traceback
from email.mime.text import MIMEText
from email.utils import parseaddr

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


def send_verification_code(recipient_email, code):
    client_id = os.getenv("GMAIL_CLIENT_ID", "").strip()
    client_secret = os.getenv("GMAIL_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN", "").strip()
    sender_email = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    mail_from = os.getenv("MAIL_FROM", "").strip()

    if not all([client_id, client_secret, refresh_token, sender_email]):
        print("EMAIL ERROR: Gmail API environment variables are missing")
        return False

    try:
        display_name, from_address = parseaddr(mail_from) if mail_from else ("", sender_email)

        if not from_address:
            from_address = sender_email

        if from_address.lower() != sender_email.lower():
            print("EMAIL ERROR: MAIL_FROM must use GMAIL_SENDER_EMAIL")
            return False

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[GMAIL_SEND_SCOPE],
        )

        service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        message = MIMEText(
            f"""Hello,

Your Employee Training Portal signup verification code is: {code}

This code expires in 10 minutes. If you did not request this code, you can ignore this email.

Regards,
Employee Training Portal"""
        )

        message["To"] = recipient_email
        message["From"] = (
            f"{display_name} <{sender_email}>"
            if display_name
            else sender_email
        )
        message["Subject"] = "Employee Training Portal - Verification Code"

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        service.users().messages().send(
            userId="me",
            body={"raw": raw_message},
        ).execute()

        print("Verification email sent successfully")
        return True

    except Exception:
        print("GMAIL API EMAIL ERROR:")
        traceback.print_exc()
        return False