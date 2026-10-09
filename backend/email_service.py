<<<<<<< HEAD
import html
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from config import Config


def _configured():
    return bool(Config.RESEND_API_KEY and Config.MAIL_FROM)


def send_email(to, subject, body, html_body=None, attachments=None):
    if not to or not _configured():
        print("EMAIL ERROR: RESEND_API_KEY or MAIL_FROM is missing")
        return False

    recipients = [to] if isinstance(to, str) else [x for x in to if x]
    if not recipients:
        print("EMAIL ERROR: no recipients")
=======

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
>>>>>>> a7b41c8 (chanhes)
        return False

    payload = {
        "from": Config.MAIL_FROM,
        "to": recipients,
        "subject": subject,
        "text": body,
    }
    if html_body:
        payload["html"] = html_body

    if attachments:
        encoded = []
        for filename, content, mimetype in attachments:
            import base64
            encoded.append({
                "filename": filename,
                "content": base64.b64encode(content).decode("ascii"),
            })
        payload["attachments"] = encoded

    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {Config.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "EmployeeTrainingPortal/1.0",
        },
        method="POST",
    )

    try:
<<<<<<< HEAD
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
            if response.status >= 200 and response.status < 300:
                print("EMAIL SENT:", result.get("id", "unknown"))
                return True
            print("EMAIL ERROR: Resend returned", response.status, result)
            return False
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = str(exc)
        print("EMAIL ERROR: Resend HTTP", exc.code, detail)
        return False
    except Exception as exc:
        print("EMAIL ERROR: Resend connection", exc)
        return False


def training_details_html(training):
    esc = lambda v: html.escape(str(v or "—"))
    return f"""
    <div style="font-family:Arial,sans-serif;line-height:1.6;color:#1f2937">
      <h2>{esc(training.get("title"))}</h2>
      <p>{esc(training.get("content"))}</p>
      <table cellpadding="8" cellspacing="0" style="border-collapse:collapse">
        <tr><td><b>Training Type</b></td><td>{esc(training.get("trainingType"))}</td></tr>
        <tr><td><b>Trainer</b></td><td>{esc(training.get("trainerName"))}</td></tr>
        <tr><td><b>Trainer Category</b></td><td>{esc(training.get("trainerCategory"))}</td></tr>
        <tr><td><b>Start</b></td><td>{esc(training.get("startDate", training.get("trainingDate")))}</td></tr>
        <tr><td><b>End</b></td><td>{esc(training.get("endDate"))}</td></tr>
        <tr><td><b>Mode</b></td><td>{esc(training.get("trainingMode"))}</td></tr>
        <tr><td><b>Venue</b></td><td>{esc(training.get("venue"))}</td></tr>
        <tr><td><b>Departments</b></td><td>{esc(", ".join(training.get("departments", [])))}</td></tr>
      </table>
      <p>Please retain this email for your training schedule.</p>
    </div>
    """


def send_training_assignment_email(employee, training):
    email = employee.get("email")
    if not email:
        return False
    subject = f"Training Scheduled: {training.get('title', 'Training')}"
    name = employee.get("name") or employee.get("employeeId") or "Employee"
    body = (
        f"Dear {name},\n\n"
        f"You have been assigned to the following training:\n\n"
        f"Training: {training.get('title','')}\n"
        f"Type: {training.get('trainingType','')}\n"
        f"Trainer: {training.get('trainerName','')}\n"
        f"Start: {training.get('startDate', training.get('trainingDate',''))}\n"
        f"End: {training.get('endDate','')}\n"
        f"Mode: {training.get('trainingMode','')}\n"
        f"Venue: {training.get('venue','')}\n"
        f"Details: {training.get('content','')}\n\n"
        "Please attend the training as scheduled.\n\n"
        "Regards,\nTraining Management Portal"
    )
    return send_email(email, subject, body, training_details_html(training))


def find_admin_emails(db):
    rows = db.users.find({"role": "HR_ADMIN"}, {"employeeId": 1, "username": 1, "_id": 0})
    emails = []
    for row in rows:
        employee = db.employees.find_one({"employeeId": row.get("employeeId")}, {"email": 1, "_id": 0}) or {}
        if employee.get("email"):
            emails.append(employee["email"])
    if Config.ADMIN_EMAIL:
        emails.append(Config.ADMIN_EMAIL)
    return list(dict.fromkeys(emails))


def send_training_admin_notification(db, training, assigned_count):
    recipients = find_admin_emails(db)
    if not recipients:
        return False
    subject = f"HR Training Notification: {training.get('title','Training')}"
    body = (
        "Dear HR/Admin,\n\n"
        f"A training has been scheduled/assigned in the Employee Training Management Portal.\n\n"
        f"Training: {training.get('title','')}\n"
        f"Type: {training.get('trainingType','')}\n"
        f"Trainer: {training.get('trainerName','')}\n"
        f"Start: {training.get('startDate',training.get('trainingDate',''))}\n"
        f"End: {training.get('endDate','')}\n"
        f"Mode: {training.get('trainingMode','')}\n"
        f"Venue: {training.get('venue','')}\n"
        f"Assigned trainees: {assigned_count}\n\n"
        "Regards,\nTraining Management Portal"
    )
    return send_email(recipients, subject, body, training_details_html(training))


def send_verification_code(email, code):
    subject = "Employee Training Portal - Email Verification Code"
    body = (
        f"Your email verification code is {code}.\n\n"
        "This code expires in 10 minutes. If you did not request an account, please ignore this email."
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif">
      <h2>Email verification</h2>
      <p>Use the following 6-digit code to complete your Employee Training Portal signup:</p>
      <div style="font-size:30px;font-weight:bold;letter-spacing:8px">{html.escape(code)}</div>
      <p>This code expires in 10 minutes.</p>
    </div>
    """
    return send_email(email, subject, body, html_body)


def send_monthly_report(db, report_month=None):
    now = datetime.now(timezone.utc)
    if report_month:
        parsed_month = datetime.strptime(report_month, "%B %Y")
        year, month = parsed_month.year, parsed_month.month
        month_label = report_month
    else:
        year, month = now.year, now.month - 1
        if month == 0:
            month, year = 12, year - 1
        month_label = datetime(year, month, 1).strftime("%B %Y")

    start_dt = datetime(year, month, 1, tzinfo=timezone.utc)
    next_dt = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 else datetime(year, month + 1, 1, tzinfo=timezone.utc)
    start_iso = start_dt.isoformat()
    next_iso = next_dt.isoformat()

    total_trainings = db.trainings.count_documents({"startDate": {"$gte": start_iso, "$lt": next_iso}})
    completed_trainings = db.trainings.count_documents({"completedAt": {"$gte": start_dt, "$lt": next_dt}})
    participants = db.training_participants.count_documents({"createdAt": {"$gte": start_dt, "$lt": next_dt}})
    attendance_marked = db.training_participants.count_documents({"attendanceMarkedAt": {"$gte": start_dt, "$lt": next_dt}})
    feedback = db.feedback.count_documents({"submittedAt": {"$gte": start_dt, "$lt": next_dt}, "status": "Submitted"})
    pending_feedback = db.training_participants.count_documents({"feedbackStatus": "Pending"})

    recipients = find_admin_emails(db)
    if not recipients:
        return False

    subject = f"Monthly Training Report - {month_label}"
    body = (
        f"Dear HR/Admin,\n\nMonthly training report for {month_label}.\n\n"
        f"Trainings scheduled: {total_trainings}\nCompleted trainings: {completed_trainings}\n"
        f"Participants assigned: {participants}\nAttendance records marked: {attendance_marked}\n"
        f"Feedback submitted: {feedback}\nCurrent feedback pending: {pending_feedback}\n\n"
        "Regards,\nTraining Management Portal"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif">
      <h2>Monthly Training Report - {html.escape(month_label)}</h2>
      <table cellpadding="10" cellspacing="0" style="border-collapse:collapse">
      <tr><td>Trainings scheduled</td><td><b>{total_trainings}</b></td></tr>
      <tr><td>Completed trainings</td><td><b>{completed_trainings}</b></td></tr>
      <tr><td>Participants assigned</td><td><b>{participants}</b></td></tr>
      <tr><td>Attendance records marked</td><td><b>{attendance_marked}</b></td></tr>
      <tr><td>Feedback submitted</td><td><b>{feedback}</b></td></tr>
      <tr><td>Current feedback pending</td><td><b>{pending_feedback}</b></td></tr>
      </table>
    </div>
    """
    return send_email(recipients, subject, body, html_body)
=======
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
>>>>>>> a7b41c8 (chanhes)
