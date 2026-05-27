from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from core.models import User, RoleEnum
from pydantic import BaseModel
from typing import Optional
from jose import jwt
from core.config import settings

router = APIRouter(prefix="/employees", tags=["Employees"])
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

class UpdateRoleRequest(BaseModel):
    role: RoleEnum

@router.get("/all")
def get_all_employees(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    employees = db.query(User).all()
    return employees

@router.delete("/{employee_id}")
def delete_employee(employee_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    employee = db.query(User).filter(User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}

@router.put("/{employee_id}/role")
def update_role(employee_id: int, req: UpdateRoleRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    employee = db.query(User).filter(User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee.role = req.role
    db.commit()
    return {"message": "Role updated successfully"}