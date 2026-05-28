from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import Report, User
from pydantic import BaseModel
from datetime import date
from typing import Optional
from jose import jwt
from core.config import settings
from datetime import date, timedelta
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/reports", tags=["Reports"])
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

class ReportRequest(BaseModel):
    date: date
    work_done: str
    pending_work: Optional[str] = None
    blockers: Optional[str] = None

@router.post("/submit")
def submit_report(req: ReportRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Report).filter(Report.user_id == user.id, Report.date == req.date).first()
    if existing:
        raise HTTPException(status_code=400, detail="Report already submitted for this date")
    report = Report(
        user_id=user.id,
        date=req.date,
        work_done=req.work_done,
        pending_work=req.pending_work,
        blockers=req.blockers
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"message": "Report submitted successfully", "report_id": report.id}

@router.get("/my-reports")
def my_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.user_id == user.id).all()
    return reports

@router.get("/team")
def team_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    reports = db.query(Report).all()
    return reports
@router.get("/filter")
def filter_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    if user.role not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    query = db.query(Report)
    if employee_id:
        query = query.filter(Report.user_id == employee_id)
    if start_date:
        query = query.filter(Report.date >= start_date)
    if end_date:
        query = query.filter(Report.date <= end_date)
    return query.all()


@router.get("/pending")
def pending_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    today = date.today()
    reports = db.query(Report).filter(Report.status == "pending").all()
    return reports
from fastapi.responses import StreamingResponse
import pandas as pd
import io

@router.get("/export/csv")
def export_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    reports = db.query(Report).all()
    data = [{
        "id": r.id,
        "user_id": r.user_id,
        "date": r.date,
        "work_done": r.work_done,
        "pending_work": r.pending_work,
        "blockers": r.blockers,
        "status": r.status
    } for r in reports]
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(stream, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=reports.csv"})

@router.get("/export/pdf")
def export_pdf(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    reports = db.query(Report).all()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "CRM KindShift - Reports")
    p.setFont("Helvetica", 10)
    y = 720
    for r in reports:
        p.drawString(50, y, f"ID: {r.id} | Date: {r.date} | User: {r.user_id} | Status: {r.status}")
        p.drawString(50, y-15, f"Work Done: {r.work_done}")
        p.drawString(50, y-30, f"Pending: {r.pending_work} | Blockers: {r.blockers}")
        y -= 60
        if y < 50:
            p.showPage()
            y = 750
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=reports.pdf"})