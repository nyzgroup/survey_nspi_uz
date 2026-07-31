# 16 kamchilik — bartaraf etish jurnali (2026-07-31)

| ID | Severity | Holat | Nima qilindi |
|----|----------|-------|--------------|
| FIND-001 | CRITICAL | FIXED | Admin parol aylantirildi; `admin123` ishlamaydi; demo_data random/env parol |
| FIND-002 | CRITICAL | FIXED | Redis `--requirepass`; URL da parol; port `127.0.0.1:6380` |
| FIND-003 | HIGH | FIXED | `safe_redirect` / `url_has_allowed_host_and_scheme` barcha login next larda |
| FIND-004 | HIGH | FIXED | `/responsibles/` ga `custom_login_required_with_token_refresh` |
| FIND-005 | HIGH | FIXED | DB parol aylantirildi; port `127.0.0.1:5433`; settings default zaif parol olib tashlandi |
| FIND-006 | HIGH | FIXED | `submit_survey_api_view` + DRF submit: `is_open` / `is_active` |
| FIND-007 | HIGH | FIXED | Choice faqat `question` bo‘yicha bog‘lanadi |
| FIND-008 | MEDIUM | FIXED | `MessageReplyView` faqat staff; message object tekshiruvi |
| FIND-009 | MEDIUM | FIXED | `/media/` protected view; authsiz 302 login |
| FIND-010 | MEDIUM | FIXED | Admin `format_html` escape (mark_safe XSS yo‘q) |
| FIND-011 | MEDIUM | FIXED | Cache rate limit: login, survey submit, message create |
| FIND-012 | MEDIUM | FIXED | CSP + Permissions-Policy middleware; SSL/HSTS env orqali |
| FIND-013 | MEDIUM | FIXED | Anonim survey: session + IP limit |
| FIND-014 | LOW | FIXED | JWT rotate + blacklist app + migrate |
| FIND-015 | LOW | FIXED | Dockerfile `appuser` (uid 1000); log `/tmp` |
| FIND-016 | LOW | FIXED | Duplicate XFrame olib tashlandi; API exception leak yopildi |

## Yangi/yangilangan fayllar
- `auth_app/security.py`
- `auth_app/media_views.py`
- `auth_app/middleware.py` (SecurityHeadersMiddleware)
- `Dockerfile`, `docker-compose.yml`, `.env.prod`, `settings.py`, `urls.py`, `views.py`, `api_views.py`, `admin.py`

## Credential
`cyber_test/CREDENTIALS_ROTATED.txt` (gitga qo‘shilmasin)
