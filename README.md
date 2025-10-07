
## 📱 Mobil Cihazlardan Erişim

Uygulamayı telefonunuzdan veya tabletiznizden kullanmak için:

### Otomatik Yöntem (Önerilen)

```bash
./start-mobile.sh
```

Bu script otomatik olarak:
- IP adresinizi algılar
- `.env.local` dosyasını günceller
- Servisleri yeniden başlatır

### Manuel Yöntem

1. IP adresinizi öğrenin:
   ```bash
   # macOS için:
   ipconfig getifaddr en0
   
   # Linux için:
   hostname -I | awk '{print $1}'
   ```

2. `.env.local` dosyasını güncelleyin:
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://SIZIN_IP_ADRESINIZ:8000" > frontend/.env.local
   ```

3. Servisleri yeniden başlatın:
   ```bash
   docker-compose restart frontend api
   ```

4. Mobil cihazınızdan şu adrese gidin:
   ```
   http://SIZIN_IP_ADRESINIZ:3000
   ```

### Önemli Notlar

- ✅ Mobil cihazınız bilgisayarınızla **aynı WiFi ağında** olmalı
- ✅ IP adresi her WiFi değişiminde güncellenmelidir
- ✅ Güvenlik duvarınız 3000 ve 8000 portlarına izin vermeli
- ⚠️ Production ortamında CORS ayarlarını sıkılaştırın

