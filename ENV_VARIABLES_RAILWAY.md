# Railway Environment Variables

Bu dosya Railway deployment için gerekli tüm environment variable'ları içerir.

## 🔧 BACKEND SERVICE

Railway Dashboard → Backend Service → Variables → Raw Editor'a aşağıdakileri yapıştırın:

```bash
MONGO_URI=mongodb+srv://okuma_admin:YOUR_PASSWORD@okuma-analizi-prod.xxxxx.mongodb.net/okuma_analizi?retryWrites=true&w=majority
MONGO_DB=okuma_analizi
REDIS_URL=redis://default:YOUR_PASSWORD@xxx.upstash.io:6379
ELEVENLABS_API_KEY=sk_2e1fdc599129486305208cb08f2fa1d92bdb2934f6bc1119
ELEVENLABS_MODEL=scribe_v1_experimental
ELEVENLABS_LANGUAGE=tr
ELEVENLABS_TEMPERATURE=0.0
ELEVENLABS_SEED=12456
ELEVENLABS_REMOVE_FILLER_WORDS=false
ELEVENLABS_REMOVE_DISFLUENCIES=false
GCS_BUCKET=doky_ai_audio_storage
GCS_PROJECT_ID=evident-airline-467110-m1
GCS_CREDENTIALS_PATH=./gcs-service-account.json
GCS_SERVICE_ACCOUNT_JSON={"type":"service_account",...FULL_JSON...}
JWT_SECRET=GENERATE_STRONG_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=43200
CORS_ORIGINS=["https://your-app.vercel.app"]
API_HOST=0.0.0.0
LOG_LEVEL=INFO
LOG_FORMAT=json
DEBUG=false
ENVIRONMENT=production
```

## ⚙️ WORKER SERVICE

Railway Dashboard → Worker Service → Variables → Raw Editor'a aşağıdakileri yapıştırın:

```bash
MONGO_URI=mongodb+srv://okuma_admin:YOUR_PASSWORD@okuma-analizi-prod.xxxxx.mongodb.net/okuma_analizi?retryWrites=true&w=majority
MONGO_DB=okuma_analizi
REDIS_URL=redis://default:YOUR_PASSWORD@xxx.upstash.io:6379
ELEVENLABS_API_KEY=sk_2e1fdc599129486305208cb08f2fa1d92bdb2934f6bc1119
ELEVENLABS_MODEL=scribe_v1_experimental
ELEVENLABS_LANGUAGE=tr
ELEVENLABS_TEMPERATURE=0.0
ELEVENLABS_SEED=12456
GCS_BUCKET=doky_ai_audio_storage
GCS_PROJECT_ID=evident-airline-467110-m1
GCS_CREDENTIALS_PATH=./gcs-service-account.json
GCS_SERVICE_ACCOUNT_JSON={"type":"service_account",...FULL_JSON...}
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 🌐 VERCEL (FRONTEND)

Vercel Dashboard → Project → Settings → Environment Variables:

```bash
NEXT_PUBLIC_API_URL=https://backend-production-xxxx.up.railway.app
```

## 📝 Notlar

1. **GCS_SERVICE_ACCOUNT_JSON:** `gcs-service-account.json` dosyasının tüm içeriğini tek satır JSON olarak yapıştırın
2. **JWT_SECRET:** Güçlü, rastgele bir secret key oluşturun (32+ karakter)
3. **CORS_ORIGINS:** Vercel deployment sonrası frontend URL'i ekleyin
4. **MongoDB & Redis URL'leri:** Atlas ve Upstash'ten alın

