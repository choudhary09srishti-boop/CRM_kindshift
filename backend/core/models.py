from sqlalchemy import Column, Integer, String, Text, Date, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"

class StatusEnum(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.employee)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reports = relationship("Report", back_populates="user")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    work_done = Column(Text, nullable=False)
    pending_work = Column(Text, nullable=True)
    blockers = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="reports")
    