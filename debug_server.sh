#!/bin/bash

# Production Server Debug Script
# Bu skript server holatini tekshiradi

echo "=== SERVER DEBUG SCRIPT ==="
echo "Date: $(date)"
echo ""

echo "1. Git repository holati:"
cd /app  # yoki loyiha papkasi
git status
echo ""

echo "2. Oxirgi commitlar:"
git log --oneline -3
echo ""

echo "3. base_api_service.py fayl tarkibi (73-qator atrofi):"
sed -n '70,80p' auth_app/services/base_api_service.py
echo ""

echo "4. isinstance tekshiruvi mavjudligi:"
grep -n "isinstance.*response_data.*dict" auth_app/services/base_api_service.py
echo ""

echo "5. Service holati:"
systemctl status your_django_app
echo ""

echo "6. Fayl o'zgarish vaqti:"
stat auth_app/services/base_api_service.py
echo ""

echo "7. Python process'lari:"
ps aux | grep python | grep -v grep
echo ""

echo "8. Port holatni tekshirish:"
netstat -tlnp | grep :8000
echo ""

echo "=== DEBUG TUGADI ==="
