import csv
import io
from datetime import datetime
from flask import Blueprint, jsonify, Response, request, send_file
from flask_jwt_extended import jwt_required, get_jwt
from bson import ObjectId
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from db import db

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")

def allowed_training(claims, training):
    if not training: return False
    if claims.get("role") == "HR_ADMIN": return True
    if claims.get("role") == "MANAGER":
        if claims.get("department") in training.get("departments", []): return True
        ids={x.get("employeeId") for x in db.employees.find({"department":claims.get("department")},{"employeeId":1,"_id":0})}
        return db.training_participants.count_documents({"trainingId":str(training["_id"]),"employeeId":{"$in":list(ids)}})>0
    return training.get("trainerEmployeeId") == claims.get("employeeId") or db.training_participants.count_documents({"trainingId":str(training["_id"]),"employeeId":claims.get("employeeId")}) > 0

def training_or_404(training_id):
    if not ObjectId.is_valid(training_id): return None
    return db.trainings.find_one({"_id": ObjectId(training_id)})

def csv_response(rows, filename):
    out=io.StringIO(); fields=list(rows[0].keys()) if rows else ["No data"]
    w=csv.DictWriter(out, fieldnames=fields); w.writeheader(); w.writerows(rows)
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

def xlsx_response(sheets, filename):
    wb=Workbook(); first=True
    for title, rows in sheets:
        ws=wb.active if first else wb.create_sheet(); first=False; ws.title=title[:31]
        if not rows:
            ws.append(["No data"]); continue
        headers=list(rows[0].keys()); ws.append(headers)
        for cell in ws[1]:
            cell.font=Font(bold=True,color="FFFFFF"); cell.fill=PatternFill("solid",fgColor="3730A3"); cell.alignment=Alignment(vertical="center")
        for row in rows:
            values=[]
            for header in headers:
                value=row.get(header, "")
                if hasattr(value, "isoformat"):
                    try: value=value.replace(tzinfo=None).isoformat(sep=" ")
                    except TypeError: value=value.isoformat()
                elif value is None: value=""
                values.append(value)
            ws.append(values)
        ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
        for col in ws.columns:
            width=min(max(max(len(str(c.value or "")) for c in col)+2,12),42)
            ws.column_dimensions[get_column_letter(col[0].column)].width=width
    output=io.BytesIO(); wb.save(output); output.seek(0)
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def attendance_rows(training_id):
    rows=[]
    for p in db.training_participants.find({"trainingId":training_id}):
        e=db.employees.find_one({"employeeId":p.get("employeeId")},{"name":1,"department":1,"_id":0}) or {}
        rows.append({"Employee ID":p.get("employeeId",""),"Employee":e.get("name",""),"Department":e.get("department",""),"Attendance":p.get("attendance","Pending"),"Marked By":p.get("attendanceMarkedBy",""),"Marked At":p.get("attendanceMarkedAt","")})
    return rows

def feedback_rows(training_id):
    rows=[]
    for f in db.feedback.find({"trainingId":training_id}).sort("submittedAt",-1):
        e=db.employees.find_one({"employeeId":f.get("employeeId")}) or {}
        t=None
        try: t=db.trainings.find_one({"_id":ObjectId(training_id)}) or {}
        except Exception: t={}
        ratings=f.get("ratings",{}) or {}
        row={
            "Employee Name":e.get("name",f.get("employeeName","")),
            "Employee ID":f.get("employeeId",""),
            "Department":e.get("department",f.get("department","")),
            "Designation":e.get("designation",f.get("designation","")),
            "Training Name":t.get("title",f.get("programme",f.get("trainingTitle",""))),
            "Training Content":t.get("content",f.get("content","")),
            "Training Type":t.get("trainingType",f.get("trainingType","")),
            "Trainer Name":t.get("trainerName",f.get("trainerName",f.get("trainer",""))),
            "Trainer Category":t.get("trainerCategory",f.get("trainerCategory","")),
            "Venue / Location":f.get("location",t.get("venue","")),
            "Training Date":f.get("dates",t.get("startDate",t.get("trainingDate",""))),
            "Training Mode":t.get("trainingMode",t.get("trainingModeType","")),
            "Trainee Names":"; ".join((db.employees.find_one({"employeeId": p.get("employeeId")}, {"name":1,"_id":0}) or {}).get("name", p.get("employeeId","")) for p in db.training_participants.find({"trainingId":training_id})),
            "Attendance":(db.training_participants.find_one({"trainingId":training_id,"employeeId":f.get("employeeId")}) or {}).get("attendance","Pending"),
            "Programme Design":ratings.get("Programme Design",""),
            "Presentation of Information":ratings.get("Presentation of Information",""),
            "Amount of Information":ratings.get("Amount of Information",""),
            "Administrative Arrangements":ratings.get("Administrative arrangements",ratings.get("Administrative Arrangements","")),
            "Overall Rating":ratings.get("overall",""),
            "Knowledge Before":f.get("knowledgeBefore",""),
            "Knowledge After":f.get("knowledgeAfter",""),
            "Best Module":f.get("bestModule",""),
            "Missed Module":f.get("missedModule",""),
            "Major Learning":f.get("majorLearning",""),
            "Ideas to Implement":f.get("ideasToImplement",""),
            "Other Remarks":f.get("remarks",""),
            "Feedback Status":f.get("status","Pending"),
            "Submitted At":f.get("submittedAt","")
        }
        # Preserve any additional questions/answers captured by older or future feedback forms.
        known=set(row)|{"_id","trainingId","employeeId","employeeName","department","trainerEmployeeId","trainerName","programme","trainingTitle","ratings","status","submittedAt"}
        for key,value in f.items():
            if key not in known:
                if isinstance(value,dict):
                    for subkey,subvalue in value.items(): row[f"{key} - {subkey}"]=subvalue
                elif isinstance(value,(list,tuple)):
                    row[key]="; ".join(str(x) for x in value)
                else: row[key]=value
        rows.append(row)
    return rows

def training_summary_rows(training_id, training):
    participants = list(db.training_participants.find({"trainingId": training_id}))
    trainee_names = []
    for participant in participants:
        employee = db.employees.find_one({"employeeId": participant.get("employeeId")}, {"name": 1, "_id": 0}) or {}
        trainee_names.append(employee.get("name") or participant.get("employeeId", ""))
    raw_date = training.get("startDate", training.get("trainingDate", ""))
    date_value = raw_date
    if hasattr(date_value, "isoformat"):
        date_value = date_value.isoformat()
    minutes = training.get("durationMinutes")
    try:
        total_hours = float(minutes) / 60 if minutes not in (None, "", 0, "0") else 0
    except (TypeError, ValueError):
        total_hours = 0
    if not total_hours and training.get("startDate") and training.get("endDate"):
        try:
            start = datetime.fromisoformat(str(training["startDate"]).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(training["endDate"]).replace("Z", "+00:00"))
            total_hours = max(0, (end - start).total_seconds() / 3600)
        except Exception:
            pass
    rows = []
    for participant in participants:
        employee = db.employees.find_one({"employeeId": participant.get("employeeId")}, {"name": 1, "_id": 0}) or {}
        rows.append({
            "Training content": training.get("content", ""),
            "Training type": training.get("trainingType", ""),
            "Trainer name": training.get("trainerName", ""),
            "Trainer - external /internal": training.get("trainerCategory", ""),
            "Trainee names": "; ".join(trainee_names),
            "Date": date_value,
            "Training mode": training.get("trainingMode", training.get("trainingModeType", "")),
            "Attendance": participant.get("attendance", "Pending"),
            "Duration": (f"{training.get('durationMinutes')} minutes" if training.get("durationMinutes") not in (None, "", 0, "0") else training.get("duration", f"{round(total_hours, 2)} hours" if total_hours else "")),
            "Total hours": round(total_hours, 2),
            "Trainee name": employee.get("name", participant.get("employeeId", "")),
            "Trainee ID": participant.get("employeeId", "")
        })
    if not rows:
        rows.append({
            "Training content": training.get("content", ""),
            "Training type": training.get("trainingType", ""),
            "Trainer name": training.get("trainerName", ""),
            "Trainer - external /internal": training.get("trainerCategory", ""),
            "Trainee names": "; ".join(trainee_names),
            "Date": date_value,
            "Training mode": training.get("trainingMode", training.get("trainingModeType", "")),
            "Attendance": "",
            "Duration": (f"{training.get('durationMinutes')} minutes" if training.get("durationMinutes") not in (None, "", 0, "0") else training.get("duration", f"{round(total_hours, 2)} hours" if total_hours else "")),
            "Total hours": round(total_hours, 2),
            "Trainee name": "",
            "Trainee ID": ""
        })
    return rows


def trainee_trainer_rows(training_id, training):
    rows=[]
    for p in db.training_participants.find({"trainingId":training_id}):
        e=db.employees.find_one({"employeeId":p.get("employeeId")},{"name":1,"department":1,"designation":1,"_id":0}) or {}
        rows.append({"Trainee ID":p.get("employeeId",""),"Trainee":e.get("name",""),"Department":e.get("department",""),"Designation":e.get("designation",""),"Trainer":training.get("trainerName",""),"Trainer Employee ID":training.get("trainerEmployeeId",""),"Attendance":p.get("attendance","Pending"),"Feedback":p.get("feedbackStatus","Pending"),"Completion":p.get("completionStatus","Not Started")})
    return rows

@reports_bp.get("/trainings")
@jwt_required()
def report_trainings():
    claims=get_jwt(); query={}
    if claims.get("role")=="MANAGER":
        ids=[x.get("employeeId") for x in db.employees.find({"department":claims.get("department")},{"employeeId":1,"_id":0}) if x.get("employeeId")]
        query["$or"]=[{"departments":claims.get("department")},{"traineeIds":{"$in":ids}}]
    elif claims.get("role")=="EMPLOYEE": query["$or"]=[{"trainerEmployeeId":claims.get("employeeId")},{"traineeIds":claims.get("employeeId")}]
    rows=[]
    for t in db.trainings.find(query).sort("startDate",-1):
        tid=str(t["_id"]); count=db.training_participants.count_documents({"trainingId":tid})
        rows.append({"_id":tid,"title":t.get("title",""),"startDate":t.get("startDate",t.get("trainingDate")),"endDate":t.get("endDate",t.get("startDate",t.get("trainingDate"))),"trainerName":t.get("trainerName",""),"trainingType":t.get("trainingType",""),"status":t.get("status","Upcoming"),"trainees":count})
    return jsonify(rows)

@reports_bp.get("/training/<training_id>/combined")
@jwt_required()
def combined_training_report(training_id):
    claims = get_jwt()
    training = training_or_404(training_id)
    if not training or not allowed_training(claims, training):
        return jsonify({"message": "Training not found or access denied"}), 403

    if request.args.get("format") == "feedback_xlsx":
        responses = feedback_rows(training_id)
        return xlsx_response([("Feedback Responses", responses)], f"{training.get('title', 'training').replace(' ', '-')}-feedback.xlsx")

    rows = training_summary_rows(training_id, training)
    if request.args.get("format") == "xlsx":
        export_rows = [{k: v for k, v in row.items() if k not in {"Trainee name", "Trainee ID"}} for row in rows]
        return xlsx_response([("Training Report", export_rows)], f"{training.get('title', 'training').replace(' ', '-')}-report.xlsx")
    display_rows = [{k: v for k, v in row.items() if k not in {"Trainee name", "Trainee ID"}} for row in rows]
    return jsonify({
        "training": {
            "id": training_id,
            "title": training.get("title", ""),
            "trainer": training.get("trainerName", ""),
            "trainingType": training.get("trainingType", ""),
            "status": training.get("status", "Upcoming")
        },
        "rows": display_rows,
        "sheets": {"training": display_rows}
    })


@reports_bp.get("/monthly.xlsx")
@jwt_required()
def monthly_report():
    claims=get_jwt(); year=request.args.get("year",str(datetime.now().year)); month_filter=request.args.get("month", "all")
    try: year=int(year)
    except ValueError: return jsonify({"message":"Year must be numeric"}),400
    query={}
    if claims.get("role")=="MANAGER":
        ids=[x.get("employeeId") for x in db.employees.find({"department":claims.get("department")},{"employeeId":1,"_id":0}) if x.get("employeeId")]
        query["$or"]=[{"departments":claims.get("department")},{"traineeIds":{"$in":ids}}]
    elif claims.get("role")=="EMPLOYEE": query["$or"]=[{"trainerEmployeeId":claims.get("employeeId")},{"traineeIds":claims.get("employeeId")}]
    trainings=list(db.trainings.find(query).sort("startDate",1))
    details=[]; monthly={m:{"Month":datetime(year,m,1).strftime("%B"),"Year":year,"Scheduled":0,"Completed":0,"Ongoing":0,"Upcoming":0,"Cancelled":0,"One-to-one / Custom":0,"Company-wide / Department":0} for m in range(1,13)}
    for t in trainings:
        raw=t.get("startDate",t.get("trainingDate")); text_date=raw.isoformat() if hasattr(raw,"isoformat") else str(raw or "")
        try: dt=datetime.fromisoformat(text_date.replace("Z","+00:00")); month=dt.month
        except Exception: continue
        if dt.year!=year: continue
        if month_filter != "all":
            try:
                if dt.month != int(month_filter): continue
            except ValueError: return jsonify({"message":"Month must be 1-12 or all"}),400
        tid=str(t["_id"]); participants=list(db.training_participants.find({"trainingId":tid})); total=len(participants)
        status=t.get("status","Upcoming")
        if status not in {"Completed","Cancelled"}:
            try: status="Ongoing" if datetime.now(dt.tzinfo or None)>=dt else "Upcoming"
            except Exception: status="Upcoming"
        scope="One-to-one / Custom" if total<=1 else "Company-wide / Department"
        a=sum(1 for p in participants if p.get("attendance") in {"Present","Partial"}); f=sum(1 for p in participants if p.get("feedbackStatus")=="Submitted")
        details.append({"Date":text_date,"Training":t.get("title",""),"Type":t.get("trainingType",""),"Trainer":t.get("trainerName",""),"Trainer ID":t.get("trainerEmployeeId",""),"Start":t.get("startDate",t.get("trainingDate")),"End":t.get("endDate",""),"Status":status,"Scope":scope,"Trainees":total,"Attendance Marked":sum(1 for p in participants if p.get("attendance") not in {None,"","Pending"}),"Present / Partial":a,"Feedback Submitted":f,"Attendance %":round(a/total*100,1) if total else 0,"Feedback Completion %":round(f/total*100,1) if total else 0})
        m=monthly[month]; m["Scheduled"]+=1; m[status]=m.get(status,0)+1
        m["One-to-one / Custom" if total<=1 else "Company-wide / Department"]+=1
    summary=list(monthly.values())
    return xlsx_response([("Monthly Summary",summary),("Training Details",details)],f"training-monthly-report-{year}.xlsx")

@reports_bp.get("/training/<training_id>/attendance")
@jwt_required()
def attendance_report(training_id):
    claims=get_jwt(); t=training_or_404(training_id)
    if not t or not allowed_training(claims,t): return jsonify({"message":"Training not found or access denied"}),403
    rows=attendance_rows(training_id)
    if request.args.get("format")=="csv": return csv_response(rows,"attendance-report.csv")
    return jsonify({"training":{"id":training_id,"title":t.get("title","" )},"rows":rows})

@reports_bp.get("/training/<training_id>/feedback")
@jwt_required()
def feedback_report(training_id):
    claims=get_jwt(); t=training_or_404(training_id)
    if not t or not allowed_training(claims,t): return jsonify({"message":"Training not found or access denied"}),403
    rows=feedback_rows(training_id)
    if request.args.get("format")=="csv": return csv_response(rows,"feedback-report.csv")
    return jsonify({"training":{"id":training_id,"title":t.get("title","" )},"rows":rows})

@reports_bp.get("/training/<training_id>/trainee-trainer")
@jwt_required()
def trainee_trainer_report(training_id):
    claims=get_jwt(); t=training_or_404(training_id)
    if not t or not allowed_training(claims,t): return jsonify({"message":"Training not found or access denied"}),403
    rows=trainee_trainer_rows(training_id,t)
    if request.args.get("format")=="csv": return csv_response(rows,"trainee-trainer-report.csv")
    return jsonify({"training":{"id":training_id,"title":t.get("title",""),"trainer":t.get("trainerName","")},"rows":rows})


@reports_bp.get("/overall.xlsx")
@jwt_required()
def overall_report():
    claims=get_jwt()
    query={}
    if claims.get("role")=="MANAGER":
        ids=[x.get("employeeId") for x in db.employees.find({"department":claims.get("department")},{"employeeId":1,"_id":0}) if x.get("employeeId")]
        query["$or"]=[{"departments":claims.get("department")},{"traineeIds":{"$in":ids}}]
    elif claims.get("role")=="EMPLOYEE":
        query["$or"]=[{"trainerEmployeeId":claims.get("employeeId")},{"traineeIds":claims.get("employeeId") }]
    start=request.args.get("fromDate","").strip(); end=request.args.get("toDate","").strip()
    try:
        start_dt=datetime.fromisoformat(start) if start else None
        end_dt=datetime.fromisoformat(end) if end else None
    except ValueError:
        return jsonify({"message":"Dates must use YYYY-MM-DD format"}),400
    if start_dt and end_dt and start_dt>end_dt:
        return jsonify({"message":"From date cannot be after To date"}),400
    details=[]
    for training in db.trainings.find(query).sort("startDate",1):
        raw = training.get("startDate", training.get("trainingDate"))
        raw_end = training.get("endDate", raw)
        def parsed(value):
            if hasattr(value, "date"): return value.replace(tzinfo=None)
            try: return datetime.fromisoformat(str(value).replace("Z","+00:00")).replace(tzinfo=None)
            except Exception: return None
        dt = parsed(raw); end_dt_value = parsed(raw_end); compare = dt or end_dt_value
        if start_dt and (not compare or compare.date() < start_dt.date()): continue
        if end_dt and (not compare or compare.date() > end_dt.date()): continue
        details.extend([{k:v for k,v in row.items() if k not in {"Trainee name","Trainee ID"}} for row in training_summary_rows(str(training["_id"]), training)])
    return xlsx_response([("Overall Training Details",details)],"overall-training-report.xlsx")
