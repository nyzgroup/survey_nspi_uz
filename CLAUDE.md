# CLAUDE.md — Survey NSPI UZ

## Loyiha nima?
NSPI universiteti uchun Django-based so'rovnoma platformasi.
Talabalar **HEMIS API** orqali login qiladi, so'rovnomalar to'ldiradi va mas'ul shaxslarga xabar yuboradi.

## Stack
- Python 3.11 · Django 4.2 · PostgreSQL 15 · Redis 7 · Celery 5.3
- Gunicorn · WhiteNoise · DRF · django-jazzmin · Bootstrap 5.3

## Ishga tushirish
```bash
docker compose up -d                                            # barcha xizmatlarni ishga tushirish
docker compose run --rm web python manage.py migrate           # migratsiya
docker compose run --rm web python manage.py create_demo_data  # demo ma'lumotlar
docker compose run --rm web python manage.py collectstatic --noinput
docker compose logs -f web                                     # loglar
docker compose down                                            # to'xtatish
```

**Admin:** http://localhost:8000/admin/ → `admin` / `admin123`

## Muhim fayllar
| Fayl | Maqsad |
|------|--------|
| `external_auth_project/settings.py` | Barcha sozlamalar (env orqali) |
| `auth_app/models.py` | Barcha modellar |
| `auth_app/views.py` | Barcha viewlar |
| `auth_app/utils.py` | `_handle_api_token_refresh`, `map_api_data_to_student_model_defaults` — YAGONA manba |
| `auth_app/decorators.py` | `custom_login_required_with_token_refresh` |
| `auth_app/tasks.py` | Celery tasklar: `sync_student_profile_from_api`, `generate_message_qr_code` |
| `auth_app/services/hemis_api_service.py` | HEMIS API client |
| `auth_app/management/commands/create_demo_data.py` | Demo ma'lumotlar buyrug'i |
| `.env.prod` | Muhit o'zgaruvchilari (git ga push qilinmasin!) |

## Modellar
- `Student` — HEMIS orqali login qilgan talabalar
- `Survey` + `Question` + `Choice` + `SurveyResponse` + `Answer` — so'rovnoma tizimi
- `ResponsiblePerson` + `MessageToResponsible` + `MessageReply` + `MessageAttachment` — xabar tizimi

## HEMIS sinxronizatsiya qoidalari (MUHIM)
`map_api_data_to_student_model_defaults()` — faqat akademik ma'lumotlar olinadi.

**Olinmaydi (saqlanmaydi):**
`passport_pin`, `passport_number`, `birth_date_timestamp`, `address_api`,
`phone`, `email`, `social_category_*`, `accommodation_*`, `validate_url_api`, `password_is_valid_api`

**Olinadi:** FISh, guruh, fakultet, yo'nalish, kurs, semestr, GPA, jins, viloyat/tuman

## Arxitektura qoidalari
- `_handle_api_token_refresh()` — **faqat** `utils.py` da, `views.py` da bo'lmasin
- `custom_login_required_with_token_refresh` — **faqat** `decorators.py` da, `views.py` da bo'lmasin
- Joriy talaba: `request.current_student` (dekorator o'rnatadi)
- Model `save()` ichida og'ir operatsiya qilinmasin — Celery ishlatilsin
- POST so'rovlar retry qilinmasin (`base_api_service.py`)
- `SECURE_SSL_REDIRECT=True` faqat nginx+SSL bo'lganda yozilsin

## .env.prod muhim sozlamalar
```
DJANGO_SECRET_KEY=...          # $ belgisi bo'lmasin (Docker buzadi)
DEBUG=False
DJANGO_ALLOWED_HOSTS=...       # production domenini qo'sh
SECURE_SSL_REDIRECT=False      # nginx+SSL bo'lganda True
HEMIS_ADMIN_API_TOKEN=...      # agar admin API kerak bo'lsa
```

## Migration holati (2026-07-17 gacha)
```
0001 → 0010  ✓ (0010 — shaxsiy maydonlar o'chirildi)
```

## Demo ma'lumotlar
- 5 talaba (student001–005), 3 so'rovnoma, 3 mas'ul shaxs, 4 javob, 3 xabar
- Qayta yaratish: `docker compose run --rm web python manage.py create_demo_data`
