from fastapi import FastAPI
from core.database import engine
from core import models
from auth.router import router as auth_router
from reports.router import router as reports_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRM KindShift API")

app.include_router(auth_router)
app.include_router(reports_router)

@app.get("/")
def root():
    return {"message": "CRM KindShift API is running"}