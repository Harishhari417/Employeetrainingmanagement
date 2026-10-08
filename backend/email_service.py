
import html
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from config import Config


def _configured():
    return bool(Config.SMTP_HOST and Config.SMTP_PORT and Config.SMTP_USERNAME and Config.SMTP_PASSWORD and Config.MAIL_FROM)


def send_email(to, subject, body, html_body=None, attachments=None):
    if not to or not _configured():
        return False
    recipients = [to] if isinstance(to, str) else [x for x in to if x]
    if not recipients:
        return False
    message = EmailMessage()
    message["From"] = Config.MAIL_FROM
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)
    if html_body:
        message.add_alternative(html_body, subtype="html")
    for filename, content, mimetype in attachments or []:
        maintype, subtype = mimetype.split("/", 1)
        message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
    try:
        if Config.SMTP_USE_TLS:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(message)
        else:
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20) as server:
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(message)
        return True
    except Exception as exc:
        print("EMAIL ERROR:", exc)
        return False


def training_details_html(training):
    esc=lambda v: html.escape(str(v or "—"))
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
        year, month = now.year, now.month
        month -= 1
        if month == 0:
            month, year = 12, year - 1
        month_label = datetime(year, month, 1).strftime("%B %Y")

    start_dt = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        next_dt = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_dt = datetime(year, month + 1, 1, tzinfo=timezone.utc)

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

