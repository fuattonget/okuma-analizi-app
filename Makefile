# Okuma Analizi Makefile
# Kullanışlı komutlar için

.PHONY: help start stop restart test clean logs build

# Varsayılan hedef
help:
	@echo "🚀 Okuma Analizi - Kullanışlı Komutlar"
	@echo "======================================"
	@echo ""
	@echo "📦 Servis Yönetimi:"
	@echo "  make start     - Sistemi başlat"
	@echo "  make stop      - Sistemi durdur"
	@echo "  make restart   - Sistemi yeniden başlat"
	@echo "  make restart-worker - Sadece worker'ı yeniden başlat"
	@echo "  make build     - Servisleri build et"
	@echo ""
	@echo "🧪 Test ve Debug:"
	@echo "  make test      - Sistem testlerini çalıştır"
	@echo "  make test-alignment - Alignment testlerini çalıştır"
	@echo "  make test-quick - Hızlı alignment testi"
	@echo "  make logs      - Tüm logları göster"
	@echo "  make logs-api  - API loglarını göster"
	@echo "  make logs-frontend - Frontend loglarını göster"
	@echo "  make logs-worker - Worker loglarını göster"
	@echo ""
	@echo "🔧 Temizlik:"
	@echo "  make clean     - Container'ları ve volume'ları temizle"
	@echo "  make clean-all - Tüm Docker kaynaklarını temizle"
	@echo ""
	@echo "🌐 Erişim:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "🌡️  Temperature Ayarları:"
	@echo "  make temp-0.0   - Temperature 0.0 (en düşük yaratıcılık)"
	@echo "  make temp-0.5   - Temperature 0.5 (orta yaratıcılık)"
	@echo "  make temp-1.0   - Temperature 1.0 (yüksek yaratıcılık)"
	@echo "  make temp-1.5   - Temperature 1.5 (en yüksek yaratıcılık)"
	@echo "  make temp-custom VALUE=0.8 - Özel temperature değeri (0.0-2.0 arası)"
	@echo "  make temp-show  - Mevcut temperature değerini göster"

# Servis yönetimi
start:
	@echo "🚀 Starting Okuma Analizi..."
	./start.sh
	@echo "🔧 Ensuring worker is running..."
	@docker-compose up -d worker

stop:
	@echo "🛑 Stopping services..."
	docker-compose down

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart
	@echo "🔧 Restarting worker..."
	docker-compose restart worker

restart-worker:
	@echo "🔧 Restarting worker only..."
	docker-compose restart worker

build:
	@echo "🔨 Building services..."
	docker-compose build

# Test
test:
	@echo "🧪 Running system tests..."
	./test-system.sh

# Alignment tests
test-alignment:
	@echo "🧪 Running alignment tests..."
	python3 run_alignment_tests.py

# Quick alignment test
test-quick:
	@echo "⚡ Running quick alignment test..."
	python3 test_alignment_quick.py

# Loglar
logs:
	@echo "📋 Showing all logs..."
	docker-compose logs -f

logs-api:
	@echo "📋 Showing API logs..."
	docker-compose logs -f api

logs-frontend:
	@echo "📋 Showing Frontend logs..."
	docker-compose logs -f frontend

logs-worker:
	@echo "📋 Showing Worker logs..."
	docker-compose logs -f worker

logs-db:
	@echo "📋 Showing Database logs..."
	docker-compose logs -f mongodb

logs-redis:
	@echo "📋 Showing Redis logs..."
	docker-compose logs -f redis

# Temizlik
clean:
	@echo "🧹 Cleaning containers and volumes..."
	docker-compose down -v
	docker system prune -f

clean-all:
	@echo "🧹 Cleaning all Docker resources..."
	docker-compose down -v --rmi all
	docker system prune -af

# Veritabanı
db-shell:
	@echo "🗄️ Opening MongoDB shell..."
	docker-compose exec mongodb mongosh okuma_analizi

db-reset:
	@echo "🗄️ Resetting database..."
	docker-compose exec mongodb mongosh --eval "db.dropDatabase()" okuma_analizi

# Geliştirme
dev:
	@echo "🔧 Starting development environment..."
	docker-compose up -d mongodb redis
	@echo "MongoDB and Redis started. Run backend and frontend locally."

# Durum kontrolü
status:
	@echo "📊 System Status:"
	@docker-compose ps
	@echo ""
	@echo "🔧 Worker Status:"
	@if docker-compose ps worker | grep -q "Up"; then \
		echo "✅ Worker is running"; \
	else \
		echo "❌ Worker is not running - starting it..."; \
		docker-compose up -d worker; \
	fi

# Hızlı test
quick-test:
	@echo "⚡ Quick API test..."
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"

# Environment setup
setup-env:
	@echo "🔧 Setting up environment files..."
	@cp env.example .env || echo "env.example not found"
	@cp backend/env.example backend/.env || echo "backend/env.example not found"
	@cp frontend/env.example frontend/.env.local || echo "frontend/env.example not found"
	@cp worker/env.example worker/.env || echo "worker/env.example not found"
	@echo "✅ Environment files created. Please edit them with your settings."

# Temperature ayarları
temp-0.0:
	@echo "🌡️  Setting temperature to 0.0 (en düşük yaratıcılık)..."
	@sed -i '' 's/ELEVENLABS_TEMPERATURE=[0-9.]*/ELEVENLABS_TEMPERATURE=0.0/g' docker-compose.yml
	@echo "✅ Temperature updated to 0.0"
	@echo "🔄 Rebuilding containers to apply changes..."
	@docker-compose down
	@docker-compose up -d --build
	@echo "✅ Containers rebuilt with temperature 0.0"

temp-0.5:
	@echo "🌡️  Setting temperature to 0.5 (orta yaratıcılık)..."
	@sed -i '' 's/ELEVENLABS_TEMPERATURE=[0-9.]*/ELEVENLABS_TEMPERATURE=0.5/g' docker-compose.yml
	@echo "✅ Temperature updated to 0.5"
	@echo "🔄 Rebuilding containers to apply changes..."
	@docker-compose down
	@docker-compose up -d --build
	@echo "✅ Containers rebuilt with temperature 0.5"

temp-1.0:
	@echo "🌡️  Setting temperature to 1.0 (yüksek yaratıcılık)..."
	@sed -i '' 's/ELEVENLABS_TEMPERATURE=[0-9.]*/ELEVENLABS_TEMPERATURE=1.0/g' docker-compose.yml
	@echo "✅ Temperature updated to 1.0"
	@echo "🔄 Rebuilding containers to apply changes..."
	@docker-compose down
	@docker-compose up -d --build
	@echo "✅ Containers rebuilt with temperature 1.0"

temp-1.5:
	@echo "🌡️  Setting temperature to 1.5 (en yüksek yaratıcılık)..."
	@sed -i '' 's/ELEVENLABS_TEMPERATURE=[0-9.]*/ELEVENLABS_TEMPERATURE=1.5/g' docker-compose.yml
	@echo "✅ Temperature updated to 1.5"
	@echo "🔄 Rebuilding containers to apply changes..."
	@docker-compose down
	@docker-compose up -d --build
	@echo "✅ Containers rebuilt with temperature 1.5"

temp-custom:
	@if [ -z "$(VALUE)" ]; then \
		echo "❌ Hata: VALUE parametresi gerekli"; \
		echo "Kullanım: make temp-custom VALUE=0.8"; \
		exit 1; \
	fi
	@if ! echo "$(VALUE)" | grep -E '^[0-9]+\.?[0-9]*$$' > /dev/null; then \
		echo "❌ Hata: Geçersiz değer. Sadece sayı girin (örn: 0.8, 1.2)"; \
		exit 1; \
	fi
	@if [ $$(echo "$(VALUE) < 0" | bc -l 2>/dev/null || echo "0") = "1" ] || [ $$(echo "$(VALUE) > 2" | bc -l 2>/dev/null || echo "0") = "1" ]; then \
		echo "❌ Hata: Temperature değeri 0.0 ile 2.0 arasında olmalı"; \
		exit 1; \
	fi
	@echo "🌡️  Setting temperature to $(VALUE) (özel değer)..."
	@sed -i '' 's/ELEVENLABS_TEMPERATURE=[0-9.]*/ELEVENLABS_TEMPERATURE=$(VALUE)/g' docker-compose.yml
	@echo "✅ Temperature updated to $(VALUE)"
	@echo "🔄 Rebuilding containers to apply changes..."
	@docker-compose down
	@docker-compose up -d --build
	@echo "✅ Containers rebuilt with temperature $(VALUE)"

temp-show:
	@echo "🌡️  Current temperature settings:"
	@echo "Docker-compose.yml:"
	@grep "ELEVENLABS_TEMPERATURE" docker-compose.yml || echo "Not found in docker-compose.yml"
	@echo ""
	@echo "Container environment:"
	@docker exec okuma-analizi-api printenv | grep ELEVENLABS_TEMPERATURE || echo "Not found in container"
	@echo ""
	@echo "Worker config:"
	@docker exec okuma-analizi-worker python3 -c "from config import settings; print(f'Temperature: {settings.elevenlabs_temperature}')" 2>/dev/null || echo "Could not read worker config"