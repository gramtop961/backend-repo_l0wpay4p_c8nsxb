import os
import csv
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field

DATA_DIR = os.path.join(os.getcwd(), "logs")
CSV_PATH = os.path.join(DATA_DIR, "contact_submissions.csv")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)


def ensure_csv_exists():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "name", "email", "message"])


@app.get("/")
def read_root():
    return {"message": "Architecture Studio API"}


@app.post("/api/contact")
async def submit_contact(payload: ContactIn):
    ensure_csv_exists()
    try:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                payload.name.strip(),
                payload.email,
                payload.message.strip().replace("\r\n", " ").replace("\n", " "),
            ])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to write submission") from e

    return {"ok": True}


@app.get("/api/contact/export")
async def export_contact_csv():
    ensure_csv_exists()
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail="No submissions yet")
    return FileResponse(
        CSV_PATH,
        media_type="text/csv",
        filename="contact_submissions.csv",
    )


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
