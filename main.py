import os
import uuid
import json
import sqlite3
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Security, HTTPException,Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from ultralytics import YOLO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# 1. Dosya ve veritabanı hazırlığı yapıyoruz
os.makedirs("uploads", exist_ok=True) # Resimlerin kaydedileceği klasör
conn = sqlite3.connect("history.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        detections TEXT,
        date_created TEXT
    )
''')
conn.commit()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Dental Caries Detection API - Secure")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Resimleri dışarı sunuyoruz (Frontend'in resimleri görebilmesi için)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

model = YOLO("best.onnx", task="detect")

@app.post("/predict_caries")
@limiter.limit("5/minute")
async def predict_caries(request: Request, file: UploadFile = File(...), api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Geçersiz API Anahtarı")
        
    # Benzersiz dosya ismi oluşturma ve kaydetme
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/{unique_filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Modeli çalıştırma ve tespitleri alma
    image = Image.open(file_path)
    results = model.predict(source=image, imgsz=1024, conf=0.25, device="cpu")
    
    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "class_id": int(box.cls[0]),
                "confidence": round(float(box.conf[0]), 3),
                "box": {"xmin": int(x1), "ymin": int(y1), "xmax": int(x2), "ymax": int(y2)}
            })
    
    # Veritabanına kaydediyoruz
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO analyses (file_path, detections, date_created) VALUES (?, ?, ?)",
                   (file_path, json.dumps(detections), now))
    conn.commit()
    
    return {"status": "success", "file_path": file_path, "detections": detections}

# 3. Geçmişi getirme rotamız bu şekilde olacak. Bu rota, analiz geçmişini JSON formatında döndürecek.
@app.get("/history")
@limiter.limit("30/minute")
async def get_history(request: Request, api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Geçersiz API Anahtarı")
        
    cursor.execute("SELECT id, file_path, detections, date_created FROM analyses ORDER BY id DESC")
    rows = cursor.fetchall()
    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "file_path": row[1],
            "detections": json.loads(row[2]),
            "date_created": row[3]
        })
    return {"status": "success", "history": history}