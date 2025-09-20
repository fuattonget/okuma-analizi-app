#!/bin/bash

# Okuma Analizi System Test Script
# Bu script sistemi test etmek için kullanılır

echo "🚀 Okuma Analizi System Test"
echo "=============================="

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test fonksiyonu
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="$3"
    
    echo -n "Testing $name... "
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$url")
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $response, expected $expected_code)"
        return 1
    fi
}

# Test sonuçları
total_tests=0
passed_tests=0

echo ""
echo "🔍 Testing Docker Services..."
echo "-----------------------------"

# Docker servislerini kontrol et
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Docker services are running${NC}"
else
    echo -e "${RED}❌ Docker services are not running${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi

echo ""
echo "🌐 Testing API Endpoints..."
echo "---------------------------"

# API Health Check
total_tests=$((total_tests + 1))
if test_endpoint "API Health" "http://localhost:8000/health" "200"; then
    passed_tests=$((passed_tests + 1))
fi

# Texts endpoint
total_tests=$((total_tests + 1))
if test_endpoint "Texts API" "http://localhost:8000/v1/texts/" "200"; then
    passed_tests=$((passed_tests + 1))
fi

# Sessions endpoint
total_tests=$((total_tests + 1))
if test_endpoint "Sessions API" "http://localhost:8000/v1/sessions/" "200"; then
    passed_tests=$((passed_tests + 1))
fi

# Analyses endpoint
total_tests=$((total_tests + 1))
if test_endpoint "Analyses API" "http://localhost:8000/v1/analyses/" "200"; then
    passed_tests=$((passed_tests + 1))
fi

# Word Events endpoint (invalid ID test)
total_tests=$((total_tests + 1))
if test_endpoint "Word Events API" "http://localhost:8000/v1/analyses/test-id/word-events" "400"; then
    passed_tests=$((passed_tests + 1))
fi

# Pause Events endpoint (invalid ID test)
total_tests=$((total_tests + 1))
if test_endpoint "Pause Events API" "http://localhost:8000/v1/analyses/test-id/pause-events" "400"; then
    passed_tests=$((passed_tests + 1))
fi

# Metrics endpoint (invalid ID test)
total_tests=$((total_tests + 1))
if test_endpoint "Metrics API" "http://localhost:8000/v1/analyses/test-id/metrics" "400"; then
    passed_tests=$((passed_tests + 1))
fi

echo ""
echo "🌍 Testing Frontend..."
echo "----------------------"

# Frontend test
total_tests=$((total_tests + 1))
if test_endpoint "Frontend" "http://localhost:3000" "200"; then
    passed_tests=$((passed_tests + 1))
fi

echo ""
echo "📊 Test Results"
echo "==============="
echo "Total Tests: $total_tests"
echo "Passed: $passed_tests"
echo "Failed: $((total_tests - passed_tests))"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}🎉 All tests passed! System is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the logs.${NC}"
    exit 1
fi

