# 🦷 DentaScan - Yapay Zeka Destekli Diş Çürüğü Tespit Sistemi

DentaScan, panoramik diş röntgenleri üzerinden derin öğrenme (YOLOv8) modeli kullanarak otomatik diş çürüğü tespiti yapan, sonuçları görselleştirip güven skorlarıyla sunan ve geçmiş analizleri kalıcı olarak saklayan uçtan uca (full-stack) bir web uygulamasıdır.

## 🚀 Özellikler
* **Anlık Analiz:** Sürükle-bırak arayüzü ile yüklenen röntgenlerde milisaniyeler içinde çürük tespiti.
* **Hassas Koordinatlama:** YOLOv8'den dönen piksel bazlı bounding-box verilerinin, responsive UI için CSS yüzdelik dilimlerine (x, y, w, h) dinamik dönüştürülmesi.
* **Geçmiş Kayıt Sistemi (Stateful):** İsteklerin ve tespitlerin SQLite veritabanında kalıcı olarak loglanması ve arayüzde listelenmesi.
* **Güvenlik & Hız Sınırlandırması (Rate Limiting):** `slowapi` kullanılarak IP bazlı DDoS koruması (Dakikada max 5 analiz isteği) ve API Anahtarı tabanlı yetkilendirme.

## 🏗️ Mimari ve Teknolojiler

Proje, modern bir Full-Stack mimarisi ile iki ayrı servis olarak tasarlanmıştır.

**Backend (Bu Depo):**
* **Framework:** FastAPI (Python)
* **Model:** YOLOv8 (ONNX formatında optimize edilmiş)
* **Veritabanı:** SQLite (Yerleşik ve sunucusuz)
* **Güvenlik:** SlowAPI (Rate Limit), FastAPI Security (Header tabanlı API Key)

**Frontend (Arayüz Deposu):**
* **Framework:** React + TypeScript + Vite
* **Routing:** TanStack Router
* **UI/UX:** Tailwind CSS, shadcn/ui, Lucide Icons

## 📡 API Dokümantasyonu

FastAPI yerleşik olarak Swagger UI sağlar. Sunucu çalışırken `http://127.0.0.1:8000/docs` adresinden test edebilirsiniz.

### 1. Yeni Analiz Oluşturma (`POST /predict_caries`)
Görüntüyü alır, analiz eder ve sonucu döner.
* **Header:** `X-API-Key: <YOUR_API_KEY>`
* **Body:** `multipart/form-data` (file: image)
* **Rate Limit:** 5 istek / dakika

**Örnek cURL İsteği:**
```bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/predict_caries](http://127.0.0.1:8000/predict_caries)' \
  -H 'X-API-Key: SECRET_KEY_BURAYA' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@test_image.jpg'
```
### 2. Geçmiş Analizleri Getirme (GET /history)
* **Veritabanındaki analiz loglarını listeler.

* **Header: X-API-Key: <YOUR_API_KEY>

Rate Limit: 30 istek / dakika  

## ⚙️ Kurulum ve Çalıştırma

### 1. Backend Kurulumu (FastAPI)
```bash
# Repoyu klonlayın
git clone https://github.com/recepdoruk58/dentascan-backend.git
cd dentascan-backend

# Sanal ortamı başlatın
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Çevre değişkenlerini yapılandırın
echo 'API_KEY="SECRET_KEY_BURAYA"' > .env

# Sunucuyu ayağa kaldırın
uvicorn main:app --host 0.0.0.0 --port 8000
```

