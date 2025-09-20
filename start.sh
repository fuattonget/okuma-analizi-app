#!/bin/bash

# Okuma Analizi Quick Start Script
# Bu script sistemi hızlıca başlatır

echo "🚀 Okuma Analizi Quick Start"
echo "============================"

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "🔧 Building and starting services..."
echo "-----------------------------------"

# Docker servislerini başlat
docker-compose up -d --build

# Worker'ın başlatıldığından emin ol
echo "🔧 Ensuring worker is started..."
docker-compose up -d worker

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi

echo ""
echo "⏳ Waiting for services to be ready..."
echo "--------------------------------------"

# Servislerin hazır olmasını bekle
sleep 10

echo ""
echo "🔍 Testing system..."
echo "-------------------"

# Test script'ini çalıştır
./test-system.sh

echo ""
echo "🌐 Access URLs:"
echo "==============="
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}Health Check:${NC} http://localhost:8000/health"

echo ""
echo "📝 Useful Commands:"
echo "==================="
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo "Restart services: docker-compose restart"
echo "Test system: ./test-system.sh"

echo ""
echo -e "${GREEN}🎉 System is ready!${NC}"

