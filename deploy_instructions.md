# 🚀 Production Server Deployment Instructions

## Muammo: AttributeError: 'str' object has no attribute 'get'

Bu xatolik `base_api_service.py` faylida 73-qatorda yuzaga kelmoqda. Server hali ham eski koddan foydalanmoqda.

## 🔧 Deployment Steps

### 1. SSH orqali serverga kirish
```bash
ssh your_user@your_production_server
```

### 2. Loyiha papkasiga o'tish
```bash
cd /app  # yoki loyiha joylashgan papka
```

### 3. Git repository holatini tekshirish
```bash
git status
git log --oneline -5  # Oxirgi 5 ta commit ko'rish
```

### 4. Yangi kodlarni olish
```bash
git fetch origin
git pull origin main
```

### 5. O'zgarishlarni tekshirish
Quyidagi fayllar o'zgargan bo'lishi kerak:
- `auth_app/services/base_api_service.py`
- `auth_app/services/hemis_api_service.py`

```bash
git show HEAD --name-only
```

### 6. Fayl mazmunini tekshirish
```bash
grep -A 10 -B 5 "isinstance(response_data, dict)" auth_app/services/base_api_service.py
```

Bu buyruq quyidagi kodni ko'rsatishi kerak:
```python
if isinstance(response_data, dict):
    api_err = response_data.get('error') or response_data.get('message') or response_data.get('detail')
    if api_err:
        error_message = str(api_err)
elif isinstance(response_data, str):
    error_message = response_data[:200] if len(response_data) > 200 else response_data
```

### 7. Virtual environment faollashtirish
```bash
source venv/bin/activate  # yoki sizning venv yo'lingiz
# yoki
source /opt/venv/bin/activate
```

### 8. Dependencies tekshirish
```bash
pip install -r requirements.txt
```

### 9. Django migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 10. Application restart
```bash
# Gunicorn/uWSGI uchun:
sudo systemctl restart your_django_app
sudo systemctl status your_django_app

# Docker uchun:
docker-compose down
docker-compose up -d

# Supervisor uchun:
sudo supervisorctl restart your_app
sudo supervisorctl status your_app
```

### 11. Loglarni kuzatish
```bash
# Real-time monitoring
tail -f /var/log/your_app/django.log

# Docker logs:
docker-compose logs -f web

# Systemd journal:
journalctl -f -u your_django_app
```

## 🧪 Test qilish

### 1. API endpoint test
```bash
curl -X POST https://student.nspi.uz/rest/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"353201107000","password":"your_password"}'
```

### 2. Web interface test
Browser orqali login sahifasiga o'ting va login qiling.

## ⚠️ Agar hali ham xatolik chiqsa:

### 1. Python cache tozalash
```bash
find /app -name "*.pyc" -delete
find /app -name "__pycache__" -type d -exec rm -rf {} +
```

### 2. Django cache tozalash
```bash
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

### 3. Hard restart
```bash
sudo systemctl stop your_django_app
sleep 5
sudo systemctl start your_django_app
```

### 4. Code verification
```bash
python -c "
import sys
sys.path.append('/app')
from auth_app.services.base_api_service import BaseAPIClient
import inspect
print(inspect.getsource(BaseAPIClient._request))
"
```

Bu kod ichida `isinstance(response_data, dict)` bo'lishi kerak.

## 🎯 Muvaffaqiyat belgilari:
- Login xatoligi yo'qolishi
- API 403 error to'g'ri handle qilinishi  
- Log'larda `AttributeError` yo'qolishi

## 📞 Qo'shimcha yordam:
Agar muammo davom etsa:
1. Server restart qiling
2. Code deploy jarayonini qaytadan bajaring
3. Debug mode'da test qiling
