# 🚀 Production Deployment Guide

Bu rehber, Okuma Analizi uygulamasını production ortamına deploy etmek için gerekli adımları içerir.

## 📋 Deployment Mimarisi

- **Frontend:** Vercel (Next.js)
- **Backend API:** Railway
- **Worker:** Railway (ayrı servis)
- **Database:** MongoDB Atlas
- **Cache/Queue:** Upstash Redis
- **Storage:** Google Cloud Storage

---

## 1️⃣ Ön Hazırlık

### Gerekli Hesaplar:
- ✅ GitHub hesabı (mevcut)
- ✅ Vercel hesabı: https://vercel.com
- ✅ Railway hesabı: https://railway.app
- ✅ MongoDB Atlas hesabı: https://www.mongodb.com/cloud/atlas
- ✅ Upstash Redis hesabı: https://console.upstash.com

---

## 2️⃣ MongoDB Atlas Setup

### Adım 1: Cluster Oluştur
1. https://www.mongodb.com/cloud/atlas/register adresine git
2. **"Build a Database"** → **Free (M0)** seç
3. **Cloud Provider:** AWS
4. **Region:** Türkiye'ye en yakın (eu-central-1 Frankfurt)
5. **Cluster Name:** `okuma-analizi-prod`
6. **Create** tıkla

### Adım 2: Database User Oluştur
1. **Database Access** → **Add New Database User**
2. **Authentication Method:** Password
3. **Username:** `okuma_admin`
4. **Password:** Güçlü bir şifre oluştur (kaydet!)
5. **Database User Privileges:** Atlas Admin
6. **Add User**

### Adım 3: Network Access
1. **Network Access** → **Add IP Address**
2. **Allow Access From Anywhere:** `0.0.0.0/0` (Production için)
3. **Confirm**

### Adım 4: Connection String Al
1. **Database** → **Connect**
2. **Drivers** seç
3. **Connection String** kopyala:
```
mongodb+srv://okuma_admin:<password>@okuma-analizi-prod.xxxxx.mongodb.net/?retryWrites=true&w=majority
```
4. `<password>` yerine gerçek şifreyi yaz
5. Database adını ekle: `/okuma_analizi?`

**Final Connection String:**
```
mongodb+srv://okuma_admin:YOUR_PASSWORD@okuma-analizi-prod.xxxxx.mongodb.net/okuma_analizi?retryWrites=true&w=majority
```

---

## 3️⃣ Upstash Redis Setup

### Adım 1: Redis Database Oluştur
1. https://console.upstash.com/ adresine git
2. **Create Database**
3. **Name:** `okuma-analizi-redis`
4. **Type:** Regional
5. **Region:** Europe (eu-west-1)
6. **Create**

### Adım 2: Connection Details Al
1. Database'i aç
2. **Redis Connect** sekmesine git
3. **Connection String** kopyala:
```
redis://default:YOUR_PASSWORD@us1-just-butterfly-12345.upstash.io:6379
```

---

## 4️⃣ Railway Backend Deployment

### Adım 1: Railway Project Oluştur
1. https://railway.app/dashboard adresine git
2. **New Project** → **Deploy from GitHub repo**
3. Repository'nizi seçin: `okuma-analizi`

### Adım 2: Backend Service Ekle
1. **Add Service** → **GitHub Repo**
2. **Root Directory:** `/backend`
3. **Dockerfile Path:** `backend/Dockerfile.railway`

### Adım 3: Environment Variables Ekle

Backend service'e tıkla → **Variables** sekmesi:

```bash
# Database
MONGO_URI=mongodb+srv://okuma_admin:YOUR_PASSWORD@okuma-analizi-prod.xxxxx.mongodb.net/okuma_analizi?retryWrites=true&w=majority
MONGO_DB=okuma_analizi

# Redis
REDIS_URL=redis://default:YOUR_PASSWORD@us1-just-butterfly-12345.upstash.io:6379

# ElevenLabs API
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

# JWT & Security
JWT_SECRET=<GENERATE_STRONG_SECRET>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=43200

# CORS (Vercel URL'inizi deploy sonrası ekleyin)
CORS_ORIGINS=["https://your-app.vercel.app","http://localhost:3000"]

# API Settings
API_HOST=0.0.0.0
API_PORT=$PORT
LOG_LEVEL=INFO
LOG_FORMAT=json
DEBUG=false
ENVIRONMENT=production
```

### Adım 4: GCS Service Account JSON Ekle
1. **Variables** → **RAW Editor**
2. Yeni satır ekle:
```
GCS_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"evident-airline-467110-m1",...}
```
3. `gcs-service-account.json` dosyasının tüm içeriğini yapıştır

### Adım 5: Deploy
1. **Deploy** butonuna tıkla
2. Logs'u izle
3. Deploy tamamlandığında **Public URL** kopyala

**Backend URL Örneği:**
```
https://okuma-analizi-backend.up.railway.app
```

---

## 5️⃣ Railway Worker Deployment

### Adım 1: Worker Service Ekle
1. Aynı Railway project'inde
2. **Add Service** → **GitHub Repo**
3. **Root Directory:** `/worker`
4. **Dockerfile Path:** `worker/Dockerfile.railway`

### Adım 2: Environment Variables Ekle

Worker service'e tıkla → **Variables**:

```bash
# Database (Backend ile aynı)
MONGO_URI=mongodb+srv://okuma_admin:YOUR_PASSWORD@okuma-analizi-prod.xxxxx.mongodb.net/okuma_analizi?retryWrites=true&w=majority
MONGO_DB=okuma_analizi

# Redis (Backend ile aynı)
REDIS_URL=redis://default:YOUR_PASSWORD@us1-just-butterfly-12345.upstash.io:6379

# ElevenLabs (Backend ile aynı)
ELEVENLABS_API_KEY=sk_2e1fdc599129486305208cb08f2fa1d92bdb2934f6bc1119
ELEVENLABS_MODEL=scribe_v1_experimental
ELEVENLABS_LANGUAGE=tr
ELEVENLABS_TEMPERATURE=0.0
ELEVENLABS_SEED=12456

# GCS (Backend ile aynı)
GCS_BUCKET=doky_ai_audio_storage
GCS_PROJECT_ID=evident-airline-467110-m1
GCS_CREDENTIALS_PATH=./gcs-service-account.json

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Adım 3: GCS Service Account JSON Ekle
Backend'deki gibi aynı JSON'ı ekle

### Adım 4: Deploy
1. **Deploy** butonuna tıkla
2. Logs'da `Worker started` mesajını gör

---

## 6️⃣ Vercel Frontend Deployment

### Adım 1: Vercel Project Oluştur
1. https://vercel.com/dashboard adresine git
2. **Add New** → **Project**
3. GitHub repository'nizi import edin

### Adım 2: Framework Settings
- **Framework Preset:** Next.js (otomatik algılanır)
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`

### Adım 3: Environment Variables

```bash
# Backend API URL (Railway'den aldığınız URL)
NEXT_PUBLIC_API_URL=https://okuma-analizi-backend.up.railway.app
```

### Adım 4: Deploy
1. **Deploy** butonuna tıkla
2. Build tamamlandığında **Visit** tıkla

**Frontend URL Örneği:**
```
https://okuma-analizi.vercel.app
```

### Adım 5: CORS Güncelleme
1. Railway Backend'e dön
2. **Variables** → `CORS_ORIGINS` güncelle:
```bash
CORS_ORIGINS=["https://okuma-analizi.vercel.app"]
```
3. Backend'i redeploy et

---

## 7️⃣ Test & Verification

### Backend Test:
```bash
curl https://okuma-analizi-backend.up.railway.app/docs
```

### Frontend Test:
1. https://okuma-analizi.vercel.app adresine git
2. Login yap
3. Analiz oluştur
4. Worker'ın çalıştığını kontrol et

### Logs Monitoring:
- **Railway Backend Logs:** Railway Dashboard → Backend Service → Logs
- **Railway Worker Logs:** Railway Dashboard → Worker Service → Logs
- **Vercel Logs:** Vercel Dashboard → Project → Deployments → Logs

---

## 8️⃣ Environment Variables Özet

### Backend & Worker Ortak Variables:
```bash
MONGO_URI=<MongoDB Atlas Connection String>
REDIS_URL=<Upstash Redis URL>
ELEVENLABS_API_KEY=sk_xxx
GCS_BUCKET=doky_ai_audio_storage
GCS_PROJECT_ID=evident-airline-467110-m1
```

### Sadece Backend:
```bash
JWT_SECRET=<Strong Secret>
CORS_ORIGINS=["https://your-vercel-app.vercel.app"]
API_PORT=$PORT
```

### Sadece Frontend:
```bash
NEXT_PUBLIC_API_URL=<Railway Backend URL>
```

---

## 🔒 Security Checklist

- [ ] MongoDB Atlas IP whitelist ayarlandı
- [ ] Güçlü JWT_SECRET kullanıldı
- [ ] CORS sadece Vercel URL'i içeriyor
- [ ] GCS credentials güvenli şekilde saklandı
- [ ] Production'da DEBUG=false
- [ ] Environment variables production için güncellendi

---

## 📊 Monitoring & Maintenance

### Railway:
- **Metrics:** CPU, Memory, Network kullanımı
- **Logs:** Real-time log streaming
- **Alerts:** Email/Slack bildirimleri ayarla

### Vercel:
- **Analytics:** Sayfa görüntülenmeleri, performans
- **Edge Functions:** Monitoring
- **Deployment Status:** Başarı/hata takibi

### MongoDB Atlas:
- **Cluster Metrics:** CPU, Disk, Connections
- **Query Performance:** Slow queries
- **Alerts:** Database health

---

## 🚨 Troubleshooting

### Backend Başlamıyor:
1. Railway logs kontrol et
2. Environment variables doğru mu?
3. MongoDB connection string geçerli mi?

### Worker Çalışmıyor:
1. Redis connection kontrol et
2. Worker logs'da hata var mı?
3. Queue'da job var mı?

### Frontend Backend'e Bağlanamıyor:
1. CORS ayarları doğru mu?
2. API URL güncel mi?
3. Backend canlı mı?

---

## 📝 Deployment Checklist

- [ ] Production branch oluşturuldu
- [ ] MongoDB Atlas setup tamamlandı
- [ ] Upstash Redis setup tamamlandı
- [ ] Railway Backend deploy edildi
- [ ] Railway Worker deploy edildi
- [ ] Vercel Frontend deploy edildi
- [ ] Environment variables ayarlandı
- [ ] CORS güncellendi
- [ ] Uygulama test edildi
- [ ] Monitoring ayarlandı

---

## 🎉 Deploy Tamamlandı!

Uygulamanız artık canlıda! 

**URLs:**
- Frontend: https://okuma-analizi.vercel.app
- Backend: https://okuma-analizi-backend.up.railway.app
- API Docs: https://okuma-analizi-backend.up.railway.app/docs

