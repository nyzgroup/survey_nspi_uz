"""
Media fayllarni autentifikatsiyasiz berishni oldini olish.
"""
import mimetypes
import os

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.views.decorators.http import require_GET

from .decorators import custom_login_required_with_token_refresh


def _is_staff_or_superuser(request) -> bool:
    user = getattr(request, "user", None)
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def _student_can_access_path(request, relative_path: str) -> bool:
    """
    Talaba faqat o'z student_id papkasidagi attachmentlarni ko'ra oladi.
    QR kodlar — login qilgan talaba/staff.
    """
    student = getattr(request, "current_student", None)
    norm = relative_path.replace("\\", "/").lstrip("/")

    if ".." in norm.split("/"):
        return False

    if norm.startswith("messages_attachments/"):
        if _is_staff_or_superuser(request):
            return True
        if not student:
            return False
        # messages_attachments/<student_id>/...
        parts = norm.split("/")
        if len(parts) >= 2 and parts[1] == str(student.id):
            return True
        return False

    if norm.startswith("message_qrcodes/"):
        # Login bo'lgan talaba yoki staff
        return bool(student or _is_staff_or_superuser(request))

    if norm.startswith("surveys/"):
        return bool(student or _is_staff_or_superuser(request))

    # Boshqa media — faqat staff
    return _is_staff_or_superuser(request)


@require_GET
@custom_login_required_with_token_refresh
def protected_media_view(request, path: str):
    """
    /media/<path> — faqat ruxsat etilgan foydalanuvchilar.
    """
    if not path or ".." in path.split("/"):
        raise Http404("Not found")

    if not _student_can_access_path(request, path):
        # Staff Django session (admin) alohida
        if _is_staff_or_superuser(request):
            pass
        else:
            return HttpResponseForbidden("Bu faylga kirish taqiqlangan.")

    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, path))
    media_root = os.path.normpath(str(settings.MEDIA_ROOT))
    if not full_path.startswith(media_root + os.sep) and full_path != media_root:
        raise Http404("Not found")
    if not os.path.isfile(full_path):
        raise Http404("Not found")

    content_type, _ = mimetypes.guess_type(full_path)
    response = FileResponse(open(full_path, "rb"), content_type=content_type or "application/octet-stream")
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = f'inline; filename="{os.path.basename(full_path)}"'
    return response


@require_GET
def protected_media_staff_or_student(request, path: str):
    """
    Admin (Django auth) yoki talaba sessiyasi bilan media.
    custom_login_required hodimni yo'naltirishi mumkin — shuning uchun alohida.
    """
    if not path or ".." in path.split("/"):
        raise Http404("Not found")

    # Django staff/superuser
    if _is_staff_or_superuser(request):
        return _serve_media_file(path)

    # Talaba sessiyasi
    api_token = request.session.get("api_token")
    student_db_id = request.session.get("student_db_id")
    if api_token and student_db_id:
        from .models import Student
        from .utils import _handle_api_token_refresh

        try:
            request.current_student = Student.objects.get(pk=student_db_id)
        except Student.DoesNotExist:
            return HttpResponseForbidden("Sessiya yaroqsiz.")
        if not _handle_api_token_refresh(request):
            return HttpResponseForbidden("Sessiya yaroqsiz.")
        if not _student_can_access_path(request, path):
            return HttpResponseForbidden("Bu faylga kirish taqiqlangan.")
        return _serve_media_file(path)

    # Hodim sessiyasi — QR va umumiy
    employee_db_id = request.session.get("employee_db_id")
    if api_token and employee_db_id:
        norm = path.replace("\\", "/").lstrip("/")
        if norm.startswith("message_qrcodes/") or norm.startswith("surveys/"):
            return _serve_media_file(path)
        if _is_staff_or_superuser(request):
            return _serve_media_file(path)
        return HttpResponseForbidden("Bu faylga kirish taqiqlangan.")

    from django.contrib.auth.views import redirect_to_login
    return redirect_to_login(request.get_full_path(), login_url="/login/")


def _serve_media_file(path: str):
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, path))
    media_root = os.path.normpath(str(settings.MEDIA_ROOT))
    if not full_path.startswith(media_root + os.sep) and full_path != media_root:
        raise Http404("Not found")
    if not os.path.isfile(full_path):
        raise Http404("Not found")
    content_type, _ = mimetypes.guess_type(full_path)
    response = FileResponse(open(full_path, "rb"), content_type=content_type or "application/octet-stream")
    response["X-Content-Type-Options"] = "nosniff"
    # XSS riskini kamaytirish: HTML/SVG attachment sifatida
    ext = os.path.splitext(full_path)[1].lower()
    if ext in {".html", ".htm", ".svg", ".xml", ".js"}:
        response["Content-Disposition"] = f'attachment; filename="{os.path.basename(full_path)}"'
        response["Content-Type"] = "application/octet-stream"
    else:
        response["Content-Disposition"] = f'inline; filename="{os.path.basename(full_path)}"'
    return response
