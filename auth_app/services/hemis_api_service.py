"""
Survey NSPI UZ — HEMIS API Service

Osiyo-Nigohi loyihasidan olingan mukammal autentifikatsiya arxitekturasi
asosida yozilgan. Asosiy farq: bu loyiha session-based (JWT emas).

HEMIS integratsiya:
  - Student SSO login   (/v1/auth/login)
  - Student profil      (/v1/account/me)
  - Admin API fallback  (/v1/data/student-list)
  - Token yangilash     (/v1/auth/refresh-token)
"""
import base64
import json as _json
import logging
import secrets
import urllib.parse
import requests
from django.conf import settings

_log = logging.getLogger("auth_app.hemis")


# ── Xatolik sinflari ────────────────────────────────────────────

class HemisAuthError(Exception):
    """Login/parol xato yoki hisob bloklangan."""
    pass


class HemisAPIError(Exception):
    """HEMIS API texnik xatosi (server, tarmoq, format)."""
    pass


class HemisRateLimitError(Exception):
    """HEMIS server IP/hisob kirish urinishlarini cheklagan (429 / CAPTCHA_REQUIRED)."""
    pass


# Backward compat — eski kod uchun
class APIClientException(Exception):
    def __init__(self, message, status_code=None, response_data=None, url=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
        self.url = url


# ── Ichki yordamchi funksiya ────────────────────────────────────

def _extract_hemis_id_from_token(token: str) -> str | None:
    """
    HEMIS JWT tokenidan hemis_id (sub/id/user_id) ni olish.

    ESLATMA: JWT imzosi TEKSHIRILMAYDI — HEMIS o'z serveridan
    qaytargan tokendan payload o'qiladi (transport xavfsizligi HTTPS
    orqali ta'minlangan). Foydalanuvchi bergan token emas.

    Returns: hemis_id string yoki None (format noto'g'ri bo'lsa).
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            _log.warning("HEMIS token JWT formatida emas (parts=%d)", len(parts))
            return None
        payload_b64 = parts[1]
        remainder = len(payload_b64) % 4
        if remainder:
            payload_b64 += "=" * (4 - remainder)
        payload = _json.loads(base64.b64decode(payload_b64))
        hemis_id = payload.get("sub") or payload.get("id") or payload.get("user_id")
        if not hemis_id:
            _log.warning("HEMIS JWT payload'da hemis_id topilmadi. keys=%s", list(payload.keys()))
        return str(hemis_id) if hemis_id else None
    except Exception as exc:
        _log.warning("HEMIS token payload decode xatosi: %s", exc)
        return None


def _hemis_base() -> str:
    return getattr(settings, 'EXTERNAL_API_BASE_URL', 'https://student.nspi.uz/rest').rstrip('/')


def _ssl_verify() -> bool:
    return getattr(settings, 'REQUESTS_VERIFY_SSL', True)


# ── Asosiy funksiyalar ──────────────────────────────────────────

def student_login(login: str, password: str) -> dict:
    """
    HEMIS SSO orqali student autentifikatsiyasi.

    Returns:
        {
          "token":       "<hemis_access_token>",
          "hemis_id":    "<hemis_user_id>" | None,
          "refresh_data": <refresh_token_cookie_data> | None,
        }
    Raises:
        HemisAuthError      — login/parol noto'g'ri (401)
        HemisRateLimitError — kirish urinishlari cheklandi (429 / CAPTCHA_REQUIRED)
        HemisAPIError       — boshqa texnik xatolik
    """
    try:
        resp = requests.post(
            f"{_hemis_base()}/v1/auth/login",
            json={"login": login, "password": password},
            timeout=15,
            verify=_ssl_verify(),
        )
    except requests.RequestException as exc:
        raise HemisAPIError(f"HEMIS serverga ulanib bo'lmadi: {exc}")

    try:
        data = resp.json()
    except Exception:
        raise HemisAPIError(f"HEMIS javobini o'qib bo'lmadi (HTTP {resp.status_code})")

    if not data.get("success"):
        code = data.get("code", 0)
        inner = (data.get("data") or {}).get("error", "")

        # Rate-limit tekshirish
        if resp.status_code == 429 or code == 429 or inner == "CAPTCHA_REQUIRED":
            _log.warning("HEMIS rate-limit (student_login) for '%s': %s", login, data.get("error"))
            raise HemisRateLimitError(
                "Tizimga kirish urinishlari soni oshib ketdi. "
                "Iltimos, bir ozdan so'ng qayta urinib ko'ring."
            )

        # Auth xatoligi
        if resp.status_code == 401 or code == 401:
            raise HemisAuthError("Login yoki parol xato.")

        msg = data.get("error") or "Noma'lum HEMIS xatosi"
        raise HemisAPIError(f"HEMIS xatosi: {msg}")

    token_data = data.get("data", {})
    token = token_data.get("token") or token_data.get("access_token", "")
    refresh_data = token_data.get("refresh_token_cookie_data")

    # hemis_id — avval API response'dan, keyin JWT payload'dan
    hemis_id = token_data.get("id") or token_data.get("user_id")
    if not hemis_id and token:
        hemis_id = _extract_hemis_id_from_token(token)

    if not hemis_id:
        _log.warning("HEMIS student_login: hemis_id aniqlanmadi. token=%s...", token[:20] if token else "")

    return {
        "token": token,
        "hemis_id": str(hemis_id) if hemis_id else None,
        "refresh_data": refresh_data,
    }


def get_student_me(hemis_token: str) -> dict:
    """
    HEMIS /v1/account/me — student to'liq profil ma'lumotlari.

    Raises:
        HemisAPIError
    """
    try:
        resp = requests.get(
            f"{_hemis_base()}/v1/account/me",
            headers={"Authorization": f"Bearer {hemis_token}"},
            timeout=15,
            verify=_ssl_verify(),
        )
    except requests.RequestException as exc:
        raise HemisAPIError(f"HEMIS /account/me ga ulanib bo'lmadi: {exc}")

    try:
        data = resp.json()
    except Exception:
        raise HemisAPIError(f"HEMIS /account/me javobini o'qib bo'lmadi (HTTP {resp.status_code})")

    if not data.get("success"):
        raise HemisAPIError(f"HEMIS /me xatosi: {data.get('error')}")

    return data["data"]


def get_student_by_login(login: str) -> dict | None:
    """
    Backend admin token bilan talabani login (student_id_number) bo'yicha izlash.

    /account/me ishlamasa yoki token bo'lmasa fallback sifatida ishlatiladi.
    HEMIS_ADMIN_API_TOKEN sozlanmagan bo'lsa None qaytaradi.
    """
    admin_token = getattr(settings, 'HEMIS_ADMIN_API_TOKEN', None)
    if not admin_token:
        return None

    try:
        resp = requests.get(
            f"{_hemis_base()}/v1/data/student-list",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"search": login, "limit": 1},
            timeout=15,
            verify=_ssl_verify(),
        )
        data = resp.json()
        if data.get("success") and (data.get("data") or {}).get("items"):
            return data["data"]["items"][0]
    except Exception as exc:
        _log.warning("get_student_by_login failed for '%s': %s", login, exc)
    return None


def refresh_auth_token(refresh_cookie_value: str) -> tuple:
    """
    Refresh token yordamida yangi access token oladi.

    Returns: (new_access_token: str, new_refresh_data)
    Raises: HemisAuthError, HemisAPIError
    """
    try:
        resp = requests.post(
            f"{_hemis_base()}/v1/auth/refresh-token",
            headers={"Cookie": refresh_cookie_value},
            timeout=15,
            verify=_ssl_verify(),
        )
    except requests.RequestException as exc:
        raise HemisAPIError(f"HEMIS refresh token ga ulanib bo'lmadi: {exc}")

    try:
        data = resp.json()
    except Exception:
        raise HemisAPIError(f"HEMIS refresh token javobini o'qib bo'lmadi (HTTP {resp.status_code})")

    if resp.status_code in [401, 403]:
        raise HemisAuthError("Refresh token yaroqsiz yoki muddati o'tgan.")

    if not data.get("success"):
        msg = data.get("error") or "Tokenni yangilashda xatolik"
        raise HemisAPIError(msg)

    token_field = (data.get("data") or {}).get("token")
    if not token_field:
        raise HemisAPIError("Yangi token javobda topilmadi.")

    new_refresh_data = (data.get("data") or {}).get("refresh_token_cookie_data")
    return token_field, new_refresh_data


def tutor_login(login: str, password: str) -> dict:
    """
    HEMIS Tutor API orqali hodim/o'qituvchi autentifikatsiyasi.
    POST /ver1/tutor/auth/login

    Returns:
        {
          "token":         "<hemis_tutor_token>",
          "refresh_token": "<refresh_token>" | None,
          "hemis_id":      "<hemis_user_id>" | None,
        }
    Raises:
        HemisAuthError      — login/parol noto'g'ri (401)
        HemisRateLimitError — kirish urinishlari cheklandi (429)
        HemisAPIError       — boshqa texnik xatolik
    """
    try:
        resp = requests.post(
            f"{_hemis_base()}/ver1/tutor/auth/login",
            json={"login": login, "password": password},
            timeout=15,
            verify=_ssl_verify(),
        )
    except requests.RequestException as exc:
        raise HemisAPIError(f"HEMIS serverga ulanib bo'lmadi: {exc}")

    try:
        data = resp.json()
    except Exception:
        raise HemisAPIError(f"HEMIS javobini o'qib bo'lmadi (HTTP {resp.status_code})")

    # Tutor API format: {"ok": bool, "status_code": int, "description": str, "data": {...}}
    if not data.get("ok"):
        status_code = data.get("status_code", 0)
        if status_code == 401 or resp.status_code == 401:
            raise HemisAuthError("Login yoki parol xato.")
        if status_code == 429 or resp.status_code == 429:
            raise HemisRateLimitError(
                "Tizimga kirish urinishlari soni oshib ketdi. "
                "Iltimos, bir ozdan so'ng qayta urinib ko'ring."
            )
        msg = data.get("description") or data.get("message") or "Noma'lum HEMIS xatosi"
        raise HemisAPIError(f"HEMIS xatosi: {msg}")

    token_data = data.get("data", {})
    token         = token_data.get("token", "")
    refresh_token = token_data.get("refresh_token", "")
    hemis_id      = _extract_hemis_id_from_token(token) if token else None

    return {
        "token":         token,
        "refresh_token": refresh_token or None,
        "hemis_id":      hemis_id,
    }


def get_tutor_profile(tutor_token: str) -> dict:
    """
    HEMIS /ver1/tutor/profile/index — hodim profil ma'lumotlari.

    Returns:
        {"tutor": {"full_name", "telephone", "email", "image", ...},
         "groups": [...], "statistics": {...}}
    Raises:
        HemisAPIError
    """
    try:
        resp = requests.get(
            f"{_hemis_base()}/ver1/tutor/profile/index",
            headers={"Authorization": f"Bearer {tutor_token}"},
            timeout=15,
            verify=_ssl_verify(),
        )
    except requests.RequestException as exc:
        raise HemisAPIError(f"HEMIS /tutor/profile ga ulanib bo'lmadi: {exc}")

    try:
        data = resp.json()
    except Exception:
        raise HemisAPIError(f"HEMIS /tutor/profile javobini o'qib bo'lmadi (HTTP {resp.status_code})")

    if not data.get("ok"):
        msg = data.get("description") or data.get("message") or "Noma'lum xato"
        raise HemisAPIError(f"HEMIS tutor profil xatosi: {msg}")

    return data.get("data") or {}


# ── HEMIS OAuth2 — Authorization Code Flow ──────────────────────
# Ikkita mustaqil OAuth server:
#   student  — student.nspi.uz  (talaba akkauntlari)
#   employee — hemis.nspi.uz    (hodim/rahbariyat akkauntlari)
# Endpointlar bir xil: /oauth/authorize, /oauth/access-token, /oauth/api/user

def _oauth_conf(portal: str) -> tuple:
    """portal ('student'|'employee') uchun (base_url, client_id, client_secret)."""
    if portal == "student":
        base = getattr(settings, 'HEMIS_STUDENT_OAUTH_BASE_URL', 'https://student.nspi.uz').rstrip('/')
        cid  = (getattr(settings, 'HEMIS_STUDENT_OAUTH_CLIENT_ID',     '') or
                getattr(settings, 'HEMIS_OAUTH_CLIENT_ID',             ''))
        csec = (getattr(settings, 'HEMIS_STUDENT_OAUTH_CLIENT_SECRET', '') or
                getattr(settings, 'HEMIS_OAUTH_CLIENT_SECRET',         ''))
    else:  # employee
        base = getattr(settings, 'HEMIS_EMPLOYEE_OAUTH_BASE_URL', 'https://hemis.nspi.uz').rstrip('/')
        cid  = getattr(settings, 'HEMIS_OAUTH_CLIENT_ID',     '')
        csec = getattr(settings, 'HEMIS_OAUTH_CLIENT_SECRET', '')
    return base, cid, csec


def generate_oauth_state() -> str:
    """Kriptografik xavfsiz 32-baytli tasodifiy state string (CSRF himoyasi)."""
    return secrets.token_urlsafe(32)


def build_hemis_oauth_url(redirect_uri: str, state: str, portal: str = "student") -> str:
    """
    HEMIS OAuth2 authorize URL yaratadi.
    Foydalanuvchi shu URLga yo'naltiriladi, login qilinganidan so'ng
    redirect_uri ga code va state bilan qaytadi.
    """
    base, client_id, _ = _oauth_conf(portal)
    params = {
        "response_type": "code",
        "client_id":     client_id,
        "redirect_uri":  redirect_uri,
        "state":         state,
    }
    scope = getattr(settings, 'HEMIS_OAUTH_SCOPE', '')
    if scope:
        params["scope"] = scope
    return f"{base}/oauth/authorize?" + urllib.parse.urlencode(params)


def hemis_oauth_exchange_code(code: str, redirect_uri: str, portal: str = "student") -> dict:
    """
    Authorization code → access token almashtirish.

    POST /oauth/access-token  (form-urlencoded, JSON emas!)
    Returns: {"access_token": "...", "token_type": "Bearer", ...}
    Raises:
        HemisAuthError — code yaroqsiz yoki muddati o'tgan (401)
        HemisAPIError  — texnik xatolik
    """
    base, client_id, client_secret = _oauth_conf(portal)
    try:
        resp = requests.post(
            f"{base}/oauth/access-token",
            data={
                "grant_type":    "authorization_code",
                "client_id":     client_id,
                "client_secret": client_secret,
                "code":          code,
                "redirect_uri":  redirect_uri,
            },
            headers={"Accept": "application/json"},
            timeout=15,
            verify=_ssl_verify(),
        )
    except requests.RequestException as exc:
        raise HemisAPIError(f"HEMIS OAuth token serverga ulanib bo'lmadi: {exc}")

    if resp.status_code == 401:
        raise HemisAuthError("OAuth code yaroqsiz yoki muddati o'tgan.")

    if not resp.ok:
        try:
            err = resp.json()
            msg = err.get("message") or err.get("error") or resp.text[:200]
        except Exception:
            msg = resp.text[:200]
        raise HemisAPIError(f"HEMIS OAuth token xatosi ({resp.status_code}): {msg}")

    data = resp.json()
    # Ba'zi HEMIS serverlar {"data": {"access_token": ...}} qaytaradi
    if "access_token" not in data and "data" in data:
        data = data["data"]

    if not data.get("access_token"):
        raise HemisAPIError("HEMIS OAuth: access_token olinmadi.")

    return data


def hemis_oauth_userinfo(access_token: str, portal: str = "student") -> dict:
    """
    HEMIS OAuth2 user info endpointi.

    GET /oauth/api/user
    Returns:
        {
          "id":                <hemis_id>,
          "type":              "student" | "employee",
          "name":              "Familiya Ism Otasining ismi",
          "login":             "<student_id_number yoki login>",
          "picture":           "<rasm URL>",
          "email":             "...",
          "phone":             "...",
          "student_api_token": "..."  (faqat talaba uchun — HEMIS SSO tokeni)
        }
    Raises:
        HemisAPIError
    """
    base, _, _ = _oauth_conf(portal)
    try:
        resp = requests.get(
            f"{base}/oauth/api/user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
            verify=_ssl_verify(),
        )
    except requests.RequestException as exc:
        raise HemisAPIError(f"HEMIS OAuth userinfo ga ulanib bo'lmadi: {exc}")

    if not resp.ok:
        raise HemisAPIError(f"HEMIS OAuth userinfo xatosi ({resp.status_code})")

    data = resp.json()
    if "id" not in data and "data" in data:
        data = data["data"]

    return data


# ── Backward compatibility wrapper ──────────────────────────────
# tasks.py va boshqa joylar uchun eski class interfeysi saqlanadi.

class HemisAPIClient:
    """
    Eski class-based wrapper — mavjud kod (tasks.py) uchun saqlanadi.
    Yangi kod uchun to'g'ridan-to'g'ri yuqoridagi funksiyalarni ishlating.
    """
    def __init__(self, api_token: str = None):
        self.api_token = api_token

    def login(self, username: str, password: str):
        """Returns: (access_token, refresh_data)"""
        try:
            result = student_login(username, password)
            return result["token"], result.get("refresh_data")
        except (HemisAuthError, HemisRateLimitError, HemisAPIError) as exc:
            raise APIClientException(str(exc))

    def get_account_me(self, api_token_override: str = None):
        token = api_token_override or self.api_token
        if not token:
            raise APIClientException("API token berilmagan.")
        try:
            return get_student_me(token)
        except (HemisAuthError, HemisAPIError) as exc:
            raise APIClientException(str(exc))

    def refresh_auth_token(self, refresh_cookie_value: str):
        try:
            return refresh_auth_token(refresh_cookie_value)
        except (HemisAuthError, HemisAPIError) as exc:
            raise APIClientException(str(exc))
