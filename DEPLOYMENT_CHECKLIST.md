# 🚀 Deployment Checklist - Adım Adım

## ✅ Tamamlanan Adımlar

- [x] Production branch oluşturuldu: `production-deployment`
- [x] Railway Backend Dockerfile hazırlandı
- [x] Railway Worker Dockerfile hazırlandı  
- [x] Railway configuration (railway.toml) oluşturuldu
- [x] Vercel configuration (vercel.json) oluşturuldu
- [x] GCS credentials environment variable desteği eklendi
- [x] Deployment guide oluşturuldu

---

## 📝 Şimdi Sıra Sizde!

### 1️⃣ MongoDB Atlas Setup (5 dakika)

**Adımlar:**
1. https://www.mongodb.com/cloud/atlas/register adresine git
2. **Build a Database** → **Free (M0)** seç
3. **Provider:** AWS, **Region:** eu-central-1 (Frankfurt)
4. **Cluster Name:** `okuma-analizi-prod`
5. **Create Cluster**

**Database User:**
1. **Database Access** → **Add New Database User**
2. **Username:** `okuma_admin`
3. **Password:** Güçlü bir şifre oluştur (kaydet!)
4. **Privileges:** Atlas Admin
5. **Add User**

**Network Access:**
1. **Network Access** → **Add IP Address**  
2. **0.0.0.0/0** (Allow from anywhere)
3. **Confirm**

**Connection String Al:**
1. **Database** → **Connect** → **Drivers**
2. Connection string'i kopyala ve şifreyi değiştir:
```
mongodb+srv://okuma_admin:YOUR_PASSWORD@okuma-analizi-prod.xxxxx.mongodb.net/okuma_analizi?retryWrites=true&w=majority
```

---

### 2️⃣ Upstash Redis Setup (3 dakika)

**Adımlar:**
1. https://console.upstash.com/ adresine git
2. **Create Database**
3. **Name:** `okuma-analizi-redis`
4. **Type:** Regional
5. **Region:** Europe (eu-west-1)
6. **Create**

**Connection String Al:**
1. Database'i aç
2. **Redis Connect** → Connection string kopyala:
```
redis://default:YOUR_PASSWORD@xxx.upstash.io:6379
```

---

### 3️⃣ Railway Backend Deploy (10 dakika)

**Railway'e Git:**
1. https://railway.app/dashboard
2. **New Project** → **Deploy from GitHub repo**
3. Repository seçin: `okuma-analizi-app`
4. Branch seçin: `production-deployment`

**Backend Service Oluştur:**
1. **Add Service** → **GitHub Repo**
2. **Service Name:** `backend`
3. **Root Directory:** Leave empty (Railway will find Dockerfile)
4. **Dockerfile Path:** `backend/Dockerfile.railway`

**Environment Variables Ekle:**

```bash
# Database
MONGO_URI=mongodb+srv://okuma_admin:YOUR_PASSWORD@okuma-analizi-prod.xxxxx.mongodb.net/okuma_analizi?retryWrites=true&w=majority
MONGO_DB=okuma_analizi

# Redis
REDIS_URL=redis://default:YOUR_PASSWORD@xxx.upstash.io:6379

# ElevenLabs
ELEVENLABS_API_KEY=sk_2e1fdc599129486305208cb08f2fa1d92bdb2934f6bc1119
ELEVENLABS_MODEL=scribe_v1_experimental
ELEVENLABS_LANGUAGE=tr
ELEVENLABS_TEMPERATURE=0.0
ELEVENLABS_SEED=12456
ELEVENLABS_REMOVE_FILLER_WORDS=false
ELEVENLABS_REMOVE_DISFLUENCIES=false

# Google Cloud Storage
GCS_BUCKET=doky_ai_audio_storage
GCS_PROJECT_ID=evident-airline-467110-m1
GCS_CREDENTIALS_PATH=./gcs-service-account.json

# ⚠️ ÖNEMLİ: GCS Service Account JSON
# gcs-service-account.json dosyasının tüm içeriğini tek satırda:
GCS_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"evident-airline-467110-m1",...FULL_JSON_HERE...}

# JWT Security
JWT_SECRET=GENERATE_STRONG_RANDOM_SECRET_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=43200

# CORS (Vercel URL'i deploy sonrası eklenecek)
CORS_ORIGINS=["http://localhost:3000"]

# API Settings
API_HOST=0.0.0.0
LOG_LEVEL=INFO
LOG_FORMAT=json
DEBUG=false
ENVIRONMENT=production
```

**Deploy:**
1. **Deploy** butonuna tıkla
2. Logs'u izle
3. ✅ "Application startup complete" mesajını bekle
4. **Public URL** kopyala (örn: `https://backend-production-xxxx.up.railway.app`)

---

### 4️⃣ Railway Worker Deploy (5 dakika)

**Worker Service Ekle:**
1. Aynı Railway project'inde
2. **Add Service** → **GitHub Repo**
3. **Service Name:** `worker`
4. **Root Directory:** Leave empty
5. **Dockerfile Path:** `worker/Dockerfile.railway`

**Environment Variables Ekle:**

```bash
# Backend ile aynı değerleri kullan
MONGO_URI=<SAME_AS_BACKEND>
MONGO_DB=okuma_analizi
REDIS_URL=<SAME_AS_BACKEND>

# ElevenLabs
ELEVENLABS_API_KEY=sk_2e1fdc599129486305208cb08f2fa1d92bdb2934f6bc1119
ELEVENLABS_MODEL=scribe_v1_experimental
ELEVENLABS_LANGUAGE=tr
ELEVENLABS_TEMPERATURE=0.0
ELEVENLABS_SEED=12456

# GCS
GCS_BUCKET=doky_ai_audio_storage
GCS_PROJECT_ID=evident-airline-467110-m1
GCS_CREDENTIALS_PATH=./gcs-service-account.json
GCS_SERVICE_ACCOUNT_JSON=<SAME_AS_BACKEND>

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Deploy:**
1. **Deploy** butonuna tıkla
2. Logs'da "Worker started" mesajını bekle

---

### 5️⃣ Vercel Frontend Deploy (7 dakika)

**Vercel'e Git:**
1. https://vercel.com/dashboard
2. **Add New** → **Project**
3. GitHub repository import et: `okuma-analizi-app`
4. Branch seçin: `production-deployment`

**Framework Settings:**
- **Framework:** Next.js (auto-detected)
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`

**Environment Variables:**

```bash
# Railway'den aldığınız backend URL
NEXT_PUBLIC_API_URL=https://backend-production-xxxx.up.railway.app
```

**Deploy:**
1. **Deploy** butonuna tıkla
2. Build tamamlanınca **Visit** tıkla
3. Frontend URL'i kopyala (örn: `https://okuma-analizi.vercel.app`)

---

### 6️⃣ CORS Güncelleme (2 dakika)

**Railway Backend'e Dön:**
1. Backend service → **Variables**
2. `CORS_ORIGINS` değişkenini güncelle:
```bash
CORS_ORIGINS=["https://okuma-analizi.vercel.app"]
```
3. **Redeploy** butonuna tıkla

---

## 🧪 Test & Verification

### Backend Test:
```bash
curl https://backend-production-xxxx.up.railway.app/docs
```
✅ Swagger UI görünmeli

### Frontend Test:
1. https://okuma-analizi.vercel.app adresine git
2. Login yap (admin hesabı)
3. Yeni analiz oluştur
4. Worker'ın çalıştığını kontrol et

### Logs:
- **Railway Backend:** Service → **Logs** → Real-time
- **Railway Worker:** Service → **Logs** → "Worker started" mesajı
- **Vercel:** Deployments → Logs

---

## 📊 Final URLs

Deployment tamamlandığında bu URL'leri doldurun:

- **Frontend:** https://_____.vercel.app
- **Backend API:** https://_____.up.railway.app
- **API Docs:** https://_____.up.railway.app/docs
- **MongoDB:** mongodb+srv://_____.mongodb.net
- **Redis:** redis://_____.upstash.io

---

## 🔒 Security Checklist

- [ ] MongoDB IP whitelist ayarlandı (0.0.0.0/0)
- [ ] Güçlü JWT_SECRET oluşturuldu
- [ ] CORS sadece Vercel URL'i içeriyor
- [ ] GCS_SERVICE_ACCOUNT_JSON Railway'e eklendi
- [ ] Production'da DEBUG=false
- [ ] Tüm şifreler güvenli yerde saklandı

---

## 🚨 Troubleshooting

### Backend Başlamıyor:
- Railway logs kontrol et
- Environment variables tamamlanmış mı?
- MongoDB connection string doğru mu?

### Worker Çalışmıyor:
- Redis connection kontrol et
- GCS_SERVICE_ACCOUNT_JSON doğru mu?
- Worker logs'da hata var mı?

### Frontend Backend'e Bağlanamıyor:
- CORS ayarları doğru mu?
- NEXT_PUBLIC_API_URL güncel mi?
- Backend canlı mı?

---

## 📞 Yardım

Detaylı rehber için: `DEPLOYMENT_GUIDE.md`

