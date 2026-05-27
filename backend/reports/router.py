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
