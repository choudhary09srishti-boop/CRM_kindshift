from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine
from core import models
from auth.router import router as auth_router
from reports.router import router as reports_router
from employees.router import router as employees_router
from employees.departments import router as departments_router
from employees.departments import Department
from core.database import Base

models.Base.metadata.create_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRM KindShift API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(employees_router)
app.include_router(departments_router)

@app.get("/")
def root():
    return {"message": "CRM KindShift API is running"}