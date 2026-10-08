
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from config import Config
from db import db
from email_service import send_monthly_report

_started = False
_lock = threading.Lock()
_last_sent = None


def start_scheduler():
    global _started
    if _started or not Config.MONTHLY_REPORT_ENABLED:
        return
    with _lock:
        if _started:
            return
        _started = True
        thread = threading.Thread(target=_loop, daemon=True, name="training-report-scheduler")
        thread.start()


def _loop():
    global _last_sent
    while True:
        try:
            now = datetime.now(ZoneInfo("Asia/Kolkata"))
            key = now.strftime("%Y-%m")
            if now.day == Config.MONTHLY_REPORT_DAY and now.hour == Config.MONTHLY_REPORT_HOUR and _last_sent != key:
                report_year, report_month = now.year, now.month - 1
                if report_month == 0:
                    report_month, report_year = 12, report_year - 1
                report_label = datetime(report_year, report_month, 1).strftime("%B %Y")
                if send_monthly_report(db, report_label):
                    _last_sent = key
        except Exception as exc:
            print("MONTHLY REPORT SCHEDULER ERROR:", exc)
        time.sleep(60)
