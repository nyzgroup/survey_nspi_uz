from django.utils import timezone
from django.conf import settings
import logging
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def get_nested(data, keys, default=None):
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current and current[key] is not None:
            current = current[key]
        else:
            return default
    return current


def map_api_data_to_student_model_defaults(api_data, current_username_or_id_number):
    """
    HEMIS API javobidan faqat akademik ma'lumotlarni oladi.
    Pasport, telefon, email, manzil va shunga o'xshash o'ta shaxsiy
    ma'lumotlar ataylab olinmaydi va saqlanmaydi.
    """
    if not isinstance(api_data, dict):
        logger.error(f"map_api_data_to_student_model_defaults kutgan ma'lumot dict emas: {type(api_data)}")
        return {}

    defaults = {
        'student_id_number': api_data.get('student_id_number', current_username_or_id_number),
        'api_user_hash': api_data.get('hash'),
        'first_name': api_data.get('first_name'),
        'last_name': api_data.get('second_name'),
        'patronymic': api_data.get('third_name'),
        'full_name_api': api_data.get('full_name'),
        'short_name_api': api_data.get('short_name'),
        'image_url': api_data.get('image'),
        'gender_code': get_nested(api_data, ['gender', 'code']),
        'gender_name': get_nested(api_data, ['gender', 'name']),
        'university_name_api': api_data.get('university'),
        'specialty_id_api': get_nested(api_data, ['specialty', 'id']),
        'specialty_code_api': get_nested(api_data, ['specialty', 'code']),
        'specialty_name_api': get_nested(api_data, ['specialty', 'name']),
        'student_status_code': get_nested(api_data, ['studentStatus', 'code']),
        'student_status_name': get_nested(api_data, ['studentStatus', 'name']),
        'education_form_code': get_nested(api_data, ['educationForm', 'code']),
        'education_form_name': get_nested(api_data, ['educationForm', 'name']),
        'education_type_code': get_nested(api_data, ['educationType', 'code']),
        'education_type_name': get_nested(api_data, ['educationType', 'name']),
        'payment_form_code': get_nested(api_data, ['paymentForm', 'code']),
        'payment_form_name': get_nested(api_data, ['paymentForm', 'name']),
        'group_id_api': get_nested(api_data, ['group', 'id']),
        'group_name_api': get_nested(api_data, ['group', 'name']),
        'group_education_lang_code': get_nested(api_data, ['group', 'educationLang', 'code']),
        'group_education_lang_name': get_nested(api_data, ['group', 'educationLang', 'name']),
        'faculty_id_api': get_nested(api_data, ['faculty', 'id']),
        'faculty_name_api': get_nested(api_data, ['faculty', 'name']),
        'faculty_code_api': get_nested(api_data, ['faculty', 'code']),
        'education_lang_code': get_nested(api_data, ['educationLang', 'code']),
        'education_lang_name': get_nested(api_data, ['educationLang', 'name']),
        'level_code': get_nested(api_data, ['level', 'code']),
        'level_name': get_nested(api_data, ['level', 'name']),
        'semester_id_api': get_nested(api_data, ['semester', 'id']),
        'semester_code_api': get_nested(api_data, ['semester', 'code']),
        'semester_name_api': get_nested(api_data, ['semester', 'name']),
        'semester_is_current': get_nested(api_data, ['semester', 'current']),
        'semester_education_year_code': get_nested(api_data, ['semester', 'education_year', 'code']),
        'semester_education_year_name': get_nested(api_data, ['semester', 'education_year', 'name']),
        'semester_education_year_is_current': get_nested(api_data, ['semester', 'education_year', 'current']),
        'avg_gpa': api_data.get('avg_gpa'),
        'country_code_api': get_nested(api_data, ['country', 'code']),
        'country_name_api': get_nested(api_data, ['country', 'name']),
        'province_code_api': get_nested(api_data, ['province', 'code']),
        'province_name_api': get_nested(api_data, ['province', 'name']),
        'district_code_api': get_nested(api_data, ['district', 'code']),
        'district_name_api': get_nested(api_data, ['district', 'name']),
        'last_login_api': timezone.now(),
    }
    return defaults


def update_student_instance_with_defaults(student_instance, defaults):
    changed_fields = []
    for key, value in defaults.items():
        if key == 'last_login_api':
            continue  # alohida boshqariladi
        if hasattr(student_instance, key) and getattr(student_instance, key) != value:
            setattr(student_instance, key, value)
            changed_fields.append(key)

    if changed_fields:
        changed_fields.append('last_login_api')
        changed_fields.append('updated_at')
        student_instance.last_login_api = defaults.get('last_login_api') or timezone.now()
        student_instance.save(update_fields=list(set(changed_fields)))
        logger.info(f"Student {student_instance.username} (ID: {student_instance.id}) updated: {changed_fields}")
    else:
        new_login_time = defaults.get('last_login_api')
        if new_login_time and student_instance.last_login_api != new_login_time:
            student_instance.last_login_api = new_login_time
            student_instance.save(update_fields=['last_login_api', 'updated_at'])
            logger.info(f"Student {student_instance.username} (ID: {student_instance.id}) last_login_api updated.")
        else:
            logger.info(f"No changes for student {student_instance.username} (ID: {student_instance.id}).")
    return student_instance


def map_api_data_to_employee_model_defaults(api_data: dict, current_username: str) -> dict:
    """
    HEMIS Tutor API /ver1/tutor/profile/index javobidan hodim model maydonlarini xaritalaydi.
    api_data — get_tutor_profile() dan qaytgan dict
    """
    if not isinstance(api_data, dict):
        logger.error(f"map_api_data_to_employee_model_defaults: kutgan ma'lumot dict emas: {type(api_data)}")
        return {}

    tutor_data = api_data.get("tutor") or api_data

    full_name = (tutor_data.get("full_name") or "").strip()
    parts = full_name.split() if full_name else []
    last_name  = parts[0] if len(parts) > 0 else None
    first_name = " ".join(parts[1:]) if len(parts) > 1 else None

    groups = api_data.get("groups") or []
    dept = (groups[0].get("department") or {}) if groups else {}

    return {
        'full_name_api':    full_name or None,
        'first_name':       first_name,
        'last_name':        last_name,
        'image_url':        tutor_data.get("image") or tutor_data.get("avatar"),
        'phone':            (tutor_data.get("telephone") or tutor_data.get("phone") or "").strip() or None,
        'email':            (tutor_data.get("email") or "").strip() or None,
        'position':         (tutor_data.get("position") or tutor_data.get("degree") or "").strip() or None,
        'department_name':  dept.get("name") or dept.get("name_uz"),
        'department_code':  str(dept.get("code", "")).strip() or None,
        'last_login_api':   timezone.now(),
    }


def update_employee_instance_with_defaults(employee_instance, defaults: dict):
    changed_fields = []
    for key, value in defaults.items():
        if key == 'last_login_api':
            continue
        if hasattr(employee_instance, key) and getattr(employee_instance, key) != value:
            setattr(employee_instance, key, value)
            changed_fields.append(key)

    if changed_fields:
        changed_fields += ['last_login_api', 'updated_at']
        employee_instance.last_login_api = defaults.get('last_login_api') or timezone.now()
        employee_instance.save(update_fields=list(set(changed_fields)))
    else:
        employee_instance.last_login_api = defaults.get('last_login_api') or timezone.now()
        employee_instance.save(update_fields=['last_login_api', 'updated_at'])
    return employee_instance


def _handle_api_token_refresh(request):
    """Token muddatini tekshirib, kerak bo'lsa yangilaydi."""
    from .services.hemis_api_service import refresh_auth_token, HemisAuthError, HemisAPIError

    refresh_cookie = request.session.get('hemis_refresh_cookie')
    current_token_expiry = request.session.get('api_token_expiry_timestamp')
    threshold = getattr(settings, 'API_TOKEN_REFRESH_THRESHOLD_SECONDS', 300)
    needs_refresh = not current_token_expiry or \
                    current_token_expiry <= timezone.now().timestamp() + threshold

    if not refresh_cookie or not needs_refresh:
        return True

    logger.info(f"Refreshing API token for session: {request.session.session_key}")
    try:
        new_access_token, new_refresh_data = refresh_auth_token(refresh_cookie)
        request.session['api_token'] = new_access_token
        expires_in = settings.SESSION_COOKIE_AGE
        if isinstance(new_refresh_data, dict) and 'expires_in' in new_refresh_data:
            try:
                expires_in = int(new_refresh_data['expires_in'])
            except (ValueError, TypeError):
                logger.warning("Invalid 'expires_in' value from refresh response.")
        request.session['api_token_expiry_timestamp'] = timezone.now().timestamp() + expires_in
        if isinstance(new_refresh_data, str):
            request.session['hemis_refresh_cookie'] = new_refresh_data
        elif isinstance(new_refresh_data, dict):
            new_cookie = new_refresh_data.get('refresh_token_cookie_value') or \
                         new_refresh_data.get('refresh_cookie')
            if new_cookie:
                request.session['hemis_refresh_cookie'] = new_cookie
        logger.info("API token successfully refreshed.")
        return True
    except HemisAuthError as exc:
        logger.warning(f"Token refresh auth error: {exc}")
        request.session.flush()
        return False
    except HemisAPIError as exc:
        logger.error(f"Token refresh API error: {exc}")
        request.session.flush()
        return False
    except Exception as exc:
        logger.critical(f"Unexpected error during token refresh: {exc}", exc_info=True)
        request.session.flush()
        return False


def generate_qr_code_image(data, prefix=""):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    filename = f"{prefix}{data}_qr.png"
    return ContentFile(buffer.getvalue(), name=filename)
