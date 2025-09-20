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
	@echo "  make build     - Servisleri build et"
	@echo ""
	@echo "🧪 Test ve Debug:"
	@echo "  make test      - Sistem testlerini çalıştır"
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

# Servis yönetimi
start:
	@echo "🚀 Starting Okuma Analizi..."
	./start.sh

stop:
	@echo "🛑 Stopping services..."
	docker-compose down

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart

build:
	@echo "🔨 Building services..."
	docker-compose build

# Test
test:
	@echo "🧪 Running system tests..."
	./test-system.sh

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