"""
Xavfsizlik yordamchilari: safe redirect, rate limit, client IP.
"""
from __future__ import annotations

import hashlib
import logging
from functools import wraps
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

logger = logging.getLogger(__name__)


def get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "unknown"


def safe_redirect_url(request, target: str | None, default: str = "/") -> str:
    """
    Open redirect oldini olish: faqat same-host yoki relative path.
    """
    if not target:
        return default

    target = str(target).strip()
    if not target:
        return default

    # javascript:, data: va boshqa sxemalarni rad etish
    lowered = target.lower()
    if lowered.startswith(("javascript:", "data:", "vbscript:")):
        logger.warning("Blocked dangerous redirect scheme: %s", target[:80])
        return default

    allowed_hosts = {request.get_host()}
    for host in getattr(settings, "ALLOWED_HOSTS", []) or []:
        if host and host != "*":
            allowed_hosts.add(host)

    require_https = request.is_secure() or getattr(settings, "SECURE_SSL_REDIRECT", False)

    if url_has_allowed_host_and_scheme(
        url=target,
        allowed_hosts=allowed_hosts,
        require_https=require_https,
    ):
        return target

    # Ba'zi brauzerlar //evil.com ni host sifatida yuboradi — rad etiladi
    parsed = urlparse(target if "://" in target else f"http:{target}" if target.startswith("//") else target)
    if parsed.scheme or parsed.netloc:
        logger.warning("Blocked open redirect to: %s", target[:120])
        return default

    if target.startswith("/") and not target.startswith("//"):
        return target

    logger.warning("Blocked open redirect to: %s", target[:120])
    return default


def safe_redirect(request, target: str | None, default: str = "/"):
    return redirect(safe_redirect_url(request, target, default=default))


def rate_limit(
    key_prefix: str,
    limit: int = 10,
    window_seconds: int = 60,
    methods: tuple[str, ...] = ("POST",),
    json_error: bool = False,
):
    """
    Cache asosidagi oddiy rate limit.
    limit ta so'rov / window_seconds oralig'ida.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.method not in methods:
                return view_func(request, *args, **kwargs)

            ip = get_client_ip(request)
            session_part = request.session.session_key or "nosession"
            raw = f"{key_prefix}:{ip}:{session_part}:{request.path}"
            cache_key = "rl:" + hashlib.sha256(raw.encode()).hexdigest()[:40]

            try:
                current = cache.get(cache_key, 0) or 0
            except Exception:
                logger.exception("Rate limit cache read failed; allowing request")
                return view_func(request, *args, **kwargs)

            if current >= limit:
                logger.warning("Rate limit exceeded prefix=%s ip=%s path=%s", key_prefix, ip, request.path)
                msg = "Juda ko'p urinish. Biroz kutib qayta urinib ko'ring."
                if json_error or request.headers.get("Accept", "").find("application/json") >= 0:
                    return JsonResponse({"status": "error", "message": msg}, status=429)
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"status": "error", "message": msg}, status=429)
                from django.contrib import messages
                messages.error(request, msg)
                # Login sahifasi uchun formani qaytarishga harakat
                if key_prefix == "login":
                    from .forms import LoginForm
                    return render(
                        request,
                        "auth_app/login.html",
                        {"form": LoginForm(), "rate_limited": True, "active_tab": "student"},
                        status=429,
                    )
                return HttpResponse(msg, status=429)

            try:
                if current == 0:
                    cache.set(cache_key, 1, timeout=window_seconds)
                else:
                    try:
                        cache.incr(cache_key)
                    except ValueError:
                        cache.set(cache_key, current + 1, timeout=window_seconds)
            except Exception:
                logger.exception("Rate limit cache write failed")

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
