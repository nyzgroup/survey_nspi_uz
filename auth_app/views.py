# auth_app/views.py
import logging
from .decorators import custom_login_required_with_token_refresh
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction, IntegrityError
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from .forms import LoginForm, create_answer_form_set
from .models import Student, Employee, Survey, SurveyResponse, Answer, Question
from .decorators import employee_login_required
from .services.hemis_api_service import (
    student_login as hemis_student_login,
    get_student_me,
    get_student_by_login,
    tutor_login as hemis_tutor_login,
    get_tutor_profile,
    generate_oauth_state,
    build_hemis_oauth_url,
    hemis_oauth_exchange_code,
    hemis_oauth_userinfo,
    HemisAuthError, HemisAPIError, HemisRateLimitError,
)
from .utils import (
    map_api_data_to_student_model_defaults,
    update_student_instance_with_defaults,
    map_api_data_to_employee_model_defaults,
    update_employee_instance_with_defaults,
    _handle_api_token_refresh,
)
from .security import safe_redirect, safe_redirect_url, rate_limit, get_client_ip

logger = logging.getLogger(__name__)
REQUESTS_VERIFY_SSL = getattr(settings, 'REQUESTS_VERIFY_SSL', True)
API_TOKEN_REFRESH_THRESHOLD_SECONDS = getattr(settings, 'API_TOKEN_REFRESH_THRESHOLD_SECONDS', 5 * 60) # default 5 daqiqa

class AuthenticationFailed(HemisAPIError):
    pass

class PermissionDeniedAPI(HemisAPIError):
    pass

# --- Helper Functions ---
def _get_error_log_id():
    return timezone.now().strftime('%Y%m%d%H%M%S%f')

# --- Views ---
@rate_limit(
    'login',
    limit=getattr(settings, 'RATE_LIMIT_LOGIN', 8),
    window_seconds=getattr(settings, 'RATE_LIMIT_LOGIN_WINDOW', 60),
    methods=('POST',),
)
def login_view(request):
    # Allaqachon kirgan foydalanuvchini yo'naltirish
    if 'api_token' in request.session:
        if 'employee_db_id' in request.session:
            return redirect('employee_home')
        if 'student_db_id' in request.session:
            if _handle_api_token_refresh(request):
                try:
                    Student.objects.get(pk=request.session['student_db_id'])
                    next_url = request.session.pop('login_next_url', None) or request.GET.get('next')
                    return safe_redirect(request, next_url, default=reverse('dashboard'))
                except Student.DoesNotExist:
                    request.session.flush()
            else:
                return redirect(settings.LOGIN_URL)

    if request.method == 'GET' and 'next' in request.GET:
        # Faqat xavfsiz next saqlanadi (open redirect oldini olish)
        request.session['login_next_url'] = safe_redirect_url(
            request, request.GET.get('next'), default=''
        ) or None

    form = LoginForm(request.POST or None)
    log_id_base = _get_error_log_id()

    if request.method == 'POST' and form.is_valid():
        username   = form.cleaned_data['username']
        password   = form.cleaned_data['password']
        login_type = request.POST.get('login_type', 'student')  # 'student' yoki 'employee'

        try:
            if login_type == 'employee':
                return _handle_employee_login(request, username, password, log_id_base)
            else:
                return _handle_student_login(request, username, password, log_id_base, form)

        except HemisAuthError as exc:
            log_id = f"{log_id_base}_AUTH"
            logger.warning(f"Log ID: {log_id} - Auth error for {username}: {exc}")
            messages.error(request, "Login yoki parol xato. Iltimos, tekshirib qayta urinib ko'ring.")

        except HemisRateLimitError as exc:
            log_id = f"{log_id_base}_RATE"
            logger.warning(f"Log ID: {log_id} - Rate limit for {username}: {exc}")
            messages.error(request, str(exc))
            return render(request, 'auth_app/login.html',
                          {'form': form, 'rate_limited': True, 'active_tab': login_type})

        except HemisAPIError as exc:
            log_id = f"{log_id_base}_API"
            logger.error(f"Log ID: {log_id} - API error for {username}: {exc}", exc_info=True)
            msg = str(exc)
            if any(t in msg.lower() for t in ["ulanib bo'lmadi", "connection", "refused"]):
                user_message = "HEMIS serveriga ulanib bo'lmadi. Internet aloqangizni tekshiring."
            elif "timeout" in msg.lower() or "vaqti tugadi" in msg.lower():
                user_message = "HEMIS serveridan javob kutish vaqti tugadi. Keyinroq urinib ko'ring."
            else:
                user_message = f"HEMIS tizimi bilan bog'lanishda xatolik. (ID: {log_id})"
            messages.error(request, user_message)

        except ValueError as exc:
            log_id = f"{log_id_base}_VAL"
            logger.error(f"Log ID: {log_id} - ValueError for {username}: {exc}", exc_info=True)
            messages.error(request, f"Ma'lumotlarni qayta ishlashda xatolik. (ID: {log_id})")

        except Exception as exc:
            log_id = f"{log_id_base}_UNEXP"
            logger.critical(f"Log ID: {log_id} - Unexpected error for {username}: {type(exc).__name__} - {exc}", exc_info=True)
            messages.error(request, f"Noma'lum tizim xatoligi. Administrator bilan bog'laning. (ID: {log_id})")

    active_tab = request.POST.get('login_type', 'student') if request.method == 'POST' else 'student'
    return render(request, 'auth_app/login.html', {'form': form, 'active_tab': active_tab})


def _handle_student_login(request, username, password, log_id_base, form):
    logger.info(f"Student login attempt: {username}")

    hemis_auth   = hemis_student_login(username, password)
    api_token    = hemis_auth["token"]
    hemis_id     = hemis_auth.get("hemis_id")
    refresh_data = hemis_auth.get("refresh_data")

    logger.info(f"HEMIS student login OK for {username}, hemis_id={hemis_id}")

    student_info = None
    if api_token:
        try:
            student_info = get_student_me(api_token)
        except HemisAPIError as exc:
            logger.warning(f"/account/me failed for {username}: {exc}. Trying admin fallback...")

    if not student_info:
        student_info = get_student_by_login(username)
        if student_info:
            logger.info(f"Admin API fallback succeeded for {username}")
        else:
            log_id = f"{log_id_base}_NODATA"
            logger.error(f"Log ID: {log_id} - Student profile not found: {username}")
            messages.error(request, f"HEMIS tizimidan ma'lumot olishda xatolik. Qayta urinib ko'ring. (ID: {log_id})")
            return render(request, 'auth_app/login.html', {'form': form, 'active_tab': 'student'})

    with transaction.atomic():
        student_defaults = map_api_data_to_student_model_defaults(student_info, username)
        if not student_defaults:
            raise ValueError("API ma'lumotlarini modellashtirishda xatolik.")
        if hemis_id:
            student_defaults['api_user_hash'] = hemis_id
        student, created = Student.objects.update_or_create(
            username=username,
            defaults=student_defaults,
        )

    request.session['api_token']         = api_token
    request.session['student_db_id']     = student.id
    request.session['username_display']  = str(student)
    request.session['student_image_url'] = student.image_url

    expires_in_login   = settings.SESSION_COOKIE_AGE
    refresh_cookie_val = None
    if isinstance(refresh_data, str):
        refresh_cookie_val = refresh_data
    elif isinstance(refresh_data, dict):
        try:
            expires_in_login = int(refresh_data.get('expires_in', expires_in_login))
        except (ValueError, TypeError):
            pass
        refresh_cookie_val = (
            refresh_data.get('refresh_token_cookie_value') or
            refresh_data.get('refresh_cookie')
        )
    request.session['api_token_expiry_timestamp'] = timezone.now().timestamp() + expires_in_login
    if refresh_cookie_val:
        request.session['hemis_refresh_cookie'] = refresh_cookie_val
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

    display_name = student_defaults.get('full_name_api') or student.username
    messages.success(request, f"Xush kelibsiz, {display_name}!")
    logger.info(f"Student {username} logged in successfully (created={created}).")

    next_url = request.session.pop('login_next_url', None) or request.GET.get('next')
    return safe_redirect(request, next_url, default=reverse('dashboard'))


def _handle_employee_login(request, username, password, log_id_base):
    logger.info(f"Employee login attempt: {username}")

    hemis_auth    = hemis_tutor_login(username, password)
    api_token     = hemis_auth["token"]
    hemis_id      = hemis_auth.get("hemis_id")
    refresh_token = hemis_auth.get("refresh_token")

    logger.info(f"HEMIS tutor login OK for {username}, hemis_id={hemis_id}")

    profile_data = {}
    if api_token:
        try:
            profile_data = get_tutor_profile(api_token)
        except HemisAPIError as exc:
            logger.warning(f"/tutor/profile failed for {username}: {exc}. Proceeding with minimal data.")

    with transaction.atomic():
        emp_defaults = map_api_data_to_employee_model_defaults(profile_data, username)
        if hemis_id:
            emp_defaults['hemis_id'] = hemis_id
        employee, created = Employee.objects.update_or_create(
            username=username,
            defaults=emp_defaults,
        )

    request.session['api_token']          = api_token
    request.session['employee_db_id']     = employee.id
    request.session['username_display']   = str(employee)
    request.session['employee_image_url'] = employee.image_url
    request.session['user_role']          = 'employee'
    if refresh_token:
        request.session['hemis_refresh_cookie'] = refresh_token
    request.session['api_token_expiry_timestamp'] = (
        timezone.now().timestamp() + settings.SESSION_COOKIE_AGE
    )
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

    display_name = emp_defaults.get('full_name_api') or employee.username
    messages.success(request, f"Xush kelibsiz, {display_name}!")
    logger.info(f"Employee {username} logged in successfully (created={created}).")

    next_url = request.session.pop('login_next_url', None) or request.GET.get('next')
    return safe_redirect(request, next_url, default=reverse('employee_home'))


def logout_view(request):
    api_token = request.session.get('api_token')
    session_key = request.session.session_key # flush dan oldin olish
    if api_token and hasattr(settings, 'EXTERNAL_API_LOGOUT_ENDPOINT') and settings.EXTERNAL_API_LOGOUT_ENDPOINT:
        try:
            client = HemisAPIClient(api_token=api_token)
            # `logout` metodi HemisAPIClient'da bo'lishi kerak va EXTERNAL_API_LOGOUT_ENDPOINT'ga so'rov yuborishi kerak.
            # Masalan, client.logout_on_api()
            # Agar API logoutni qo'llab-quvvatlamasa, bu qismni olib tashlash kerak.
            # client.logout_on_api() # Bu metod mavjud deb faraz qilamiz
            logger.info(f"API token (if supported by API) might be invalidated for session {session_key}")
        except APIClientException as e:
            logger.warning(f"Failed to invalidate API token on API-side logout for session {session_key}: {e}")
        except Exception:
            logger.warning(f"Unexpected error during API-side logout for session {session_key}", exc_info=True)

    request.session.flush()
    messages.info(request, "Siz tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect(settings.LOGIN_URL)


def home_view(request):
    if 'api_token' in request.session:
        if 'employee_db_id' in request.session:
            return redirect('employee_home')
        if 'student_db_id' in request.session:
            if _handle_api_token_refresh(request):
                return redirect('dashboard')
            return redirect(settings.LOGIN_URL)
    return render(request, 'auth_app/home.html')


@employee_login_required
def employee_home_view(request):
    employee = request.current_employee
    context = {'employee': employee}
    return render(request, 'auth_app/employee_home.html', context)


def oauth_init_view(request):
    """
    HEMIS OAuth2 ga yo'naltirish.
    GET /oauth/init/?portal=student|employee

    State ni Redis cachega saqlaydi (10 daqiqa), keyin HEMIS authorize URL
    ga redirect qiladi.
    """
    portal = request.GET.get('portal', 'student')
    if portal not in ('student', 'employee'):
        portal = 'student'

    if not getattr(settings, 'HEMIS_OAUTH_CLIENT_ID', ''):
        messages.error(request, "OAuth2 konfiguratsiyasi to'liq emas. Administrator bilan bog'laning.")
        return redirect('login')

    state        = generate_oauth_state()
    redirect_uri = _oauth_redirect_uri(request)

    # State ni Redis/cache da 10 daqiqa saqlaymiz (CSRF himoyasi)
    cache.set(f"hemis_oauth_state:{state}", portal, timeout=600)

    authorize_url = build_hemis_oauth_url(redirect_uri, state, portal=portal)
    logger.info(f"OAuth init: portal={portal}, redirecting to HEMIS authorize.")
    return redirect(authorize_url)


def oauth_callback_view(request):
    """
    HEMIS OAuth2 callback.
    GET /oauth/callback/?code=...&state=...

    Jarayon:
      1. State tekshirish (CSRF himoyasi)
      2. Code → access_token almashtirish
      3. User info olish
      4. Student yoki Employee model yaratish/yangilash
      5. Django sessiyasini boshlash
      6. Dashboard yoki employee_home ga yo'naltirish
    """
    error = request.GET.get('error', '').strip()
    if error:
        desc = request.GET.get('error_description', error)
        messages.error(request, f"HEMIS OAuth xatosi: {desc}")
        return redirect('login')

    code  = request.GET.get('code',  '').strip()
    state = request.GET.get('state', '').strip()

    if not code or not state:
        messages.error(request, "OAuth callback: majburiy parametrlar yo'q.")
        return redirect('login')

    # State validatsiya (CSRF)
    cache_key     = f"hemis_oauth_state:{state}"
    cached_portal = cache.get(cache_key)
    if not cached_portal:
        messages.error(request, "OAuth state yaroqsiz yoki muddati o'tgan. Qaytadan urinib ko'ring.")
        return redirect('login')
    cache.delete(cache_key)

    portal       = cached_portal if cached_portal in ('student', 'employee') else 'student'
    redirect_uri = _oauth_redirect_uri(request)
    log_id_base  = _get_error_log_id()

    try:
        # 1. Code → access token
        token_data   = hemis_oauth_exchange_code(code, redirect_uri, portal=portal)
        oauth_token  = token_data["access_token"]

        # 2. User info
        oauth_user   = hemis_oauth_userinfo(oauth_token, portal=portal)
        hemis_id     = str(oauth_user.get("id", "")).strip()
        user_type    = (oauth_user.get("type") or portal).lower()

        if not hemis_id:
            messages.error(request, "HEMIS OAuth: foydalanuvchi ID olinmadi.")
            return redirect('login')

        logger.info(f"OAuth callback OK: hemis_id={hemis_id}, type={user_type}, portal={portal}")

        if user_type == "student":
            return _handle_oauth_student_login(request, oauth_user, oauth_token, hemis_id)
        else:
            return _handle_oauth_employee_login(request, oauth_user, oauth_token, hemis_id)

    except HemisAuthError as exc:
        log_id = f"{log_id_base}_OA"
        logger.warning(f"Log ID: {log_id} - OAuth auth error: {exc}")
        messages.error(request, "OAuth autentifikatsiya xatosi. Qaytadan urinib ko'ring.")

    except HemisAPIError as exc:
        log_id = f"{log_id_base}_OI"
        logger.error(f"Log ID: {log_id} - OAuth API error: {exc}", exc_info=True)
        msg = str(exc)
        if "ulanib bo'lmadi" in msg or "connection" in msg.lower():
            messages.error(request, "HEMIS serveriga ulanib bo'lmadi.")
        else:
            messages.error(request, f"HEMIS tizimi bilan bog'lanishda xatolik. (ID: {log_id})")

    except Exception as exc:
        log_id = f"{log_id_base}_OU"
        logger.critical(f"Log ID: {log_id} - OAuth unexpected: {type(exc).__name__} - {exc}", exc_info=True)
        messages.error(request, f"Noma'lum tizim xatoligi. (ID: {log_id})")

    return redirect('login')


def _oauth_redirect_uri(request) -> str:
    """OAuth callback URL — settings dagi HEMIS_OAUTH_REDIRECT_URI yoki request dan."""
    explicit = getattr(settings, 'HEMIS_OAUTH_REDIRECT_URI', '').strip()
    if explicit:
        return explicit
    return request.build_absolute_uri(reverse('oauth_callback'))


def _handle_oauth_student_login(request, oauth_user, oauth_token, hemis_id):
    """OAuth talaba login — Student yaratish/yangilash, sessiya boshlash."""
    login    = (oauth_user.get("login") or "").strip()
    username = login or f"oauth_{hemis_id}"

    # student_api_token bilan to'liq profil olishga urinamiz
    student_info      = None
    student_api_token = (oauth_user.get("student_api_token") or "").strip()

    if student_api_token:
        try:
            student_info = get_student_me(student_api_token)
        except HemisAPIError:
            pass

    # Fallback: admin API dan login bo'yicha izlash
    if not student_info and login:
        student_info = get_student_by_login(login)

    # Minimal ma'lumot bilan ishlash (profil endpoint ishlamasa ham)
    if not student_info:
        full_name = (oauth_user.get("name") or "").strip()
        parts = full_name.split()
        student_info = {
            "full_name":        full_name,
            "first_name":       parts[1] if len(parts) > 1 else "",
            "second_name":      parts[0] if parts else "",
            "image":            (oauth_user.get("picture") or "").strip(),
            "student_id_number": login,
        }

    # Sessiya uchun asosiy token: student_api_token > oauth_token
    api_token = student_api_token or oauth_token

    with transaction.atomic():
        student_defaults = map_api_data_to_student_model_defaults(student_info, username)
        if hemis_id:
            student_defaults['api_user_hash'] = hemis_id
        student, created = Student.objects.update_or_create(
            username=username,
            defaults=student_defaults,
        )

    request.session['api_token']         = api_token
    request.session['student_db_id']     = student.id
    request.session['username_display']  = str(student)
    request.session['student_image_url'] = student.image_url
    request.session['api_token_expiry_timestamp'] = (
        timezone.now().timestamp() + settings.SESSION_COOKIE_AGE
    )
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

    display_name = student_defaults.get('full_name_api') or student.username
    messages.success(request, f"Xush kelibsiz, {display_name}!")
    logger.info(f"Student {username} logged in via OAuth (created={created}).")

    next_url = request.session.pop('login_next_url', None)
    return safe_redirect(request, next_url, default=reverse('dashboard'))


def _handle_oauth_employee_login(request, oauth_user, oauth_token, hemis_id):
    """OAuth hodim login — Employee yaratish/yangilash, sessiya boshlash."""
    login    = (oauth_user.get("login") or "").strip()
    username = login or f"oauth_emp_{hemis_id}"

    full_name = (oauth_user.get("name") or "").strip()
    parts     = full_name.split() if full_name else []

    emp_defaults = {
        'hemis_id':      hemis_id,
        'full_name_api': full_name or None,
        'last_name':     parts[0] if parts else None,
        'first_name':    " ".join(parts[1:]) if len(parts) > 1 else None,
        'image_url':     (oauth_user.get("picture") or "").strip() or None,
        'email':         (oauth_user.get("email") or "").strip() or None,
        'phone':         (oauth_user.get("phone") or "").strip() or None,
        'last_login_api': timezone.now(),
    }

    with transaction.atomic():
        employee, created = Employee.objects.update_or_create(
            username=username,
            defaults=emp_defaults,
        )

    request.session['api_token']          = oauth_token
    request.session['employee_db_id']     = employee.id
    request.session['username_display']   = str(employee)
    request.session['employee_image_url'] = employee.image_url
    request.session['user_role']          = 'employee'
    request.session['api_token_expiry_timestamp'] = (
        timezone.now().timestamp() + settings.SESSION_COOKIE_AGE
    )
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

    display_name = emp_defaults.get('full_name_api') or employee.username
    messages.success(request, f"Xush kelibsiz, {display_name}!")
    logger.info(f"Employee {username} logged in via OAuth (created={created}).")

    next_url = request.session.pop('login_next_url', None)
    return safe_redirect(request, next_url, default=reverse('employee_home'))


@custom_login_required_with_token_refresh
def dashboard_view(request):
    current_student = getattr(request, 'current_student', None) # Dekorator o'rnatadi

    if not current_student: # Bu holat kamdan-kam yuz berishi kerak
        logger.error(f"FATAL: current_student not found in request for dashboard despite decorator. Session: {request.session.session_key}")
        request.session.flush()
        messages.error(request, "Kritik sessiya xatoligi. Iltimos, qayta kiring.")
        return redirect(settings.LOGIN_URL)
    
    # Dashboardga har kirganda profilni yangilash (agar kerak bo'lsa va interval o'tgan bo'lsa)
    # Bu foydalanuvchi uchun yuklamani oshirishi mumkin. Celery task afzalroq.
    # refresh_interval = timezone.timedelta(minutes=getattr(settings, "DASHBOARD_PROFILE_REFRESH_INTERVAL_MINUTES", 30))
    # last_updated_threshold = timezone.now() - refresh_interval

    # if current_student.updated_at < last_updated_threshold:
    #     logger.info(f"Student {current_student.username} profile data is older than {refresh_interval}. Attempting refresh.")
    #     try:
    #         api_client = HemisAPIClient(api_token=request.session.get('api_token')) # Token sessiyadan olinadi
    #         student_info_from_api = api_client.get_account_me()
    #         if student_info_from_api and isinstance(student_info_from_api, dict):
    #             student_defaults = map_api_data_to_student_model_defaults(student_info_from_api, current_student.username)
    #             if student_defaults:
    #                 update_student_instance_with_defaults(current_student, student_defaults)
    #                 # current_student ni qayta yuklash kerak emas, chunki update_student_instance_with_defaults o'zgartiradi
    #                 messages.info(request, "Profil ma'lumotlaringiz yangilandi.")
    #             else:
    #                 logger.warning(f"Could not map API data for student {current_student.username} during dashboard refresh.")
    #         else:
    #             logger.warning(f"No data or invalid data from API for {current_student.username} during dashboard refresh.")
    #     except APIClientException as e:
    #         messages.warning(request, f"Profilni API dan yangilab bo'lmadi: {e.args[0]}")
    #         logger.error(f"APIClientException during dashboard profile refresh for {current_student.username}: {e}", exc_info=True)
    #     except Exception as e:
    #         logger.error(f"Unexpected error during dashboard profile refresh for {current_student.username}: {e}", exc_info=True)
    #         messages.error(request, "Profilni yangilashda kutilmagan xatolik yuz berdi.")

    # Statistika ma'lumotlarini hisoblash
    from .models import Survey, SurveyResponse
    
    # Faol so'rovnomalar soni
    total_surveys = Survey.objects.filter(is_active=True).count()
    
    # Talaba tomonidan tugatilgan so'rovnomalar
    if current_student:
        completed_surveys = SurveyResponse.objects.filter(student=current_student).count()
        # Kutilayotgan so'rovnomalar (umumiy faol - tugatilgan)
        pending_surveys = max(0, total_surveys - completed_surveys)
        # Ishtirok darajasi
        participation_rate = round((completed_surveys / total_surveys * 100) if total_surveys > 0 else 0, 1)
    else:
        completed_surveys = 0
        pending_surveys = total_surveys
        participation_rate = 0

    context = {
        'student': current_student, # Endi bu yangilangan bo'lishi mumkin
        'username_display': str(current_student),
        'total_surveys': total_surveys,
        'completed_surveys': completed_surveys,
        'pending_surveys': pending_surveys,
        'participation_rate': participation_rate,
    }
    return render(request, 'auth_app/dashboard.html', context)

def _process_survey_submission(request, survey, student, formset):
    """
    So'rovnoma javoblarini atomik tranzaksiya ichida qayta ishlaydi va saqlaydi.
    Samaradorlik uchun `bulk_create` ishlatiladi.
    """
    try:
        with transaction.atomic():
            survey_response_data = {'survey': survey}
            if not survey.is_anonymous:
                survey_response_data['student'] = student
            survey_response = SurveyResponse.objects.create(**survey_response_data)

            answers_to_create = []
            for form in formset:
                if not form.has_changed() or not form.is_valid():
                    continue
                if not hasattr(form, 'question_instance'):
                    continue

                answer = form.save(commit=False)
                answer.survey_response = survey_response
                answer.question = form.question_instance
                answers_to_create.append(answer)

            if not answers_to_create:
                messages.warning(request, "Hech qanday javob yuborilmadi.")
                return False

            Answer.objects.bulk_create(answers_to_create)

            logger.info(f"Saved {len(answers_to_create)} answers for SurveyResponse ID: {survey_response.pk}")
            messages.success(request, f"'{survey.title}' so'rovnomasiga javoblaringiz qabul qilindi. Rahmat!")
            return True

    except IntegrityError:
        logger.warning(f"IntegrityError on survey submission. Survey: {survey.pk}, Student: {student.pk}")
        messages.error(request, "Siz bu so'rovnomada avval qatnashgansiz.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing survey submission. Survey: {survey.pk}, Error: {e}", exc_info=True)
        messages.error(request, "Javoblarni saqlashda kutilmagan xatolik yuz berdi.")
        return False

###############################
# auth_app/views.py
# ... (mavjud importlar va viewlar) ...

# ... (login_view, logout_view, home_view, dashboard_view, _handle_api_token_refresh, custom_login_required_with_token_refresh oldingidek) ...

@custom_login_required_with_token_refresh
def survey_list_view(request):
    """Aktiv so'rovnomalar ro'yxatini ko'rsatadi."""
    now = timezone.now()
    surveys = Survey.objects.filter(is_active=True, start_date__lte=now).exclude(end_date__isnull=False, end_date__lt=now).order_by('-start_date')
    student = request.current_student

    responded_survey_ids = SurveyResponse.objects.filter(student=student, survey__in=surveys).values_list('survey_id', flat=True)
    
    surveys_with_status = [{ 'survey': survey, 'has_responded': survey.id in responded_survey_ids } for survey in surveys]

    context = {
        'surveys_with_status': surveys_with_status,
        'student': student,
        'username_display': str(student),
    }
    return render(request, 'auth_app/survey_list.html', context)


# auth_app/views.py

# --- Django va standart kutubxona importlari ---
import json
import logging
from functools import wraps

from django.conf import settings
from django.contrib import messages


@custom_login_required_with_token_refresh
def survey_detail_view(request, survey_pk):
    """
    Bu view HTML render qilmaydi. U bo'sh shablonni va so'rovnoma ma'lumotlarini
    JSON formatida tayyorlab, JavaScript'ga uzatish uchun javobgar.
    """
    survey = get_object_or_404(Survey.objects.prefetch_related('questions__choices'), pk=survey_pk)
    student = request.current_student

    # --- Dastlabki tekshiruvlar ---
    if not survey.is_open:
        messages.error(request, "Bu so'rovnoma hozirda mavjud emas yoki muddati tugagan.")
        return redirect('survey_list')

    if not survey.is_anonymous:
        if SurveyResponse.objects.filter(survey=survey, student=student).exists():
            messages.info(request, f"Siz '{survey.title}' so'rovnomasida avval ishtirok etgansiz.")
            return redirect('survey_list')

    # --- Ma'lumotlarni JavaScript uchun JSON formatiga o'tkazish ---
    survey_data = {
        'id': survey.id,
        'title': survey.title,
        'description': survey.description,
        'questions': []
    }

    # Savollarni samarali yuklash uchun .all() ishlatamiz
    questions = survey.questions.all()
    for question in questions:
        q_data = {
            'id': question.id,
            'text': question.text,
            'question_type': question.question_type,
            'is_required': question.is_required,
            'choices': [{'id': choice.id, 'text': choice.text} for choice in question.choices.all()]
        }
        survey_data['questions'].append(q_data)

    # --- Context'ga JSON va CSRF tokenini qo'shish ---
    context = {
        'survey': survey,
        # json.dumps XSS uchun xavfsiz; mark_safe faqat JSON struktura uchun
        'survey_data_json': mark_safe(json.dumps(survey_data, ensure_ascii=False).replace('<', '\\u003c')),
        'csrf_token': get_token(request),  # CSRF tokenini to'g'ridan-to'g'ri uzatish
        'student': student,
        'username_display': str(student),
    }
    return render(request, 'auth_app/survey_detail.html', context)


@csrf_protect  # CSRF himoyasini qo'lda ta'minlaydi
@custom_login_required_with_token_refresh
@rate_limit(
    'survey_submit',
    limit=getattr(settings, 'RATE_LIMIT_SURVEY_SUBMIT', 20),
    window_seconds=60,
    methods=('POST',),
    json_error=True,
)
def submit_survey_api_view(request, survey_pk):
    """
    JavaScript'dan AJAX/Fetch orqali kelgan JSON javoblarni qabul qiladigan API endpoint.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Faqat POST so\'rovlariga ruxsat etilgan.'}, status=405)

    survey = get_object_or_404(Survey, pk=survey_pk)
    student = request.current_student

    # Server-side: yopiq / nofaol so'rovnomaga javob berish taqiqlanadi (FIND-006)
    if not getattr(survey, 'is_active', True) or not survey.is_open:
        return JsonResponse({
            'status': 'error',
            'message': "Bu so'rovnoma hozirda mavjud emas yoki muddati tugagan.",
        }, status=403)

    # Qayta ishtirok etishni tekshirish (poyga holatlari uchun muhim)
    if not survey.is_anonymous and SurveyResponse.objects.filter(survey=survey, student=student).exists():
        return JsonResponse({'status': 'error', 'message': 'Siz bu so\'rovnomada avval qatnashgansiz.'}, status=400)

    # Anonim so'rovnoma: bir sessiya + IP bo'yicha qayta ovoz cheklovi (FIND-013)
    from django.core.cache import cache
    anon_cache_key = None
    if survey.is_anonymous:
        if not request.session.session_key:
            request.session.create()
        anon_cache_key = f"anon_survey_done:{survey.pk}:{request.session.session_key}"
        if cache.get(anon_cache_key):
            return JsonResponse({
                'status': 'error',
                'message': "Siz bu anonim so'rovnomada ushbu sessiyada avval qatnashgansiz.",
            }, status=400)
        ip_key = f"anon_survey_ip:{survey.pk}:{get_client_ip(request)}"
        ip_count = cache.get(ip_key, 0) or 0
        if ip_count >= 5:
            return JsonResponse({
                'status': 'error',
                'message': "Bu so'rovnoma uchun juda ko'p urinish aniqlandi. Keyinroq urinib ko'ring.",
            }, status=429)

    try:
        data = json.loads(request.body)
        answers_data = data.get('answers', {})

        # Hech bo'lmasa bitta javob borligini tekshirish
        if not answers_data or not any(answers_data.values()):
             return JsonResponse({'status': 'error', 'message': 'Iltimos, kamida bitta savolga javob bering.'}, status=400)

        # Majburiy savollar uchun validation
        questions_map = {q.id: q for q in survey.questions.all()}
        for question in questions_map.values():
            if question.is_required:
                question_answer = answers_data.get(str(question.id))
                if not question_answer or (isinstance(question_answer, str) and not question_answer.strip()) or (isinstance(question_answer, list) and not question_answer):
                    return JsonResponse({'status': 'error', 'message': f'"{question.text}" savoliga javob berish majburiy!'}, status=400)

        from .models import Choice

        with transaction.atomic():
            survey_response = SurveyResponse.objects.create(
                survey=survey,
                student=student if not survey.is_anonymous else None
            )

            for question_id_str, value in answers_data.items():
                question_id = int(question_id_str)
                question = questions_map.get(question_id)

                if not question or (isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value):
                    continue  # Bo'sh javoblarni o'tkazib yuborish

                answer = Answer(survey_response=survey_response, question=question)

                if question.question_type == 'text':
                    answer.text_answer = str(value)
                    answer.save()
                elif question.question_type == 'single_choice':
                    # Choice faqat shu savolga tegishli bo'lishi shart (FIND-007)
                    try:
                        choice = Choice.objects.get(pk=int(value), question=question)
                    except (Choice.DoesNotExist, ValueError, TypeError):
                        raise ValueError(f"Noto'g'ri variant: question={question_id}")
                    answer.selected_choice = choice
                    answer.save()
                elif question.question_type == 'multiple_choice' and isinstance(value, list):
                    answer.save()  # M2M bog'lanishidan oldin asosiy obyekt saqlanishi shart
                    choice_ids = [int(cid) for cid in value]
                    valid_choices = list(question.choices.filter(id__in=choice_ids))
                    if len(valid_choices) != len(set(choice_ids)):
                        raise ValueError(f"Noto'g'ri variantlar: question={question_id}")
                    answer.selected_choices.set(valid_choices)

        if survey.is_anonymous and anon_cache_key:
            cache.set(anon_cache_key, 1, timeout=60 * 60 * 24 * 30)  # 30 kun
            ip_key = f"anon_survey_ip:{survey.pk}:{get_client_ip(request)}"
            try:
                if cache.get(ip_key) is None:
                    cache.set(ip_key, 1, timeout=60 * 60 * 24)
                else:
                    cache.incr(ip_key)
            except Exception:
                cache.set(ip_key, 1, timeout=60 * 60 * 24)

        # Foydalanuvchiga redirectdan so'ng xabar ko'rsatish
        messages.success(request, f"'{survey.title}' so'rovnomasiga javoblaringiz muvaffaqiyatli yuborildi. Rahmat!")
        return JsonResponse({'status': 'success', 'redirect_url': reverse('survey_list')})

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
         logger.warning(f"Survey submission - yaroqsiz ma'lumotlar. Xato: {e}", exc_info=False)
         return JsonResponse({'status': 'error', 'message': 'Yuborilgan ma\'lumotlar formati noto\'g\'ri.'}, status=400)
    except Exception as e:
        logger.error(f"Survey submission API'da kutilmagan xatolik: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Javoblarni saqlashda serverda xatolik yuz berdi.'}, status=500)
    

# auth_app/views.py

# Mavjud importlarga qo'shimcha:
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser # Faqat adminlar uchun
from .models import Survey, SurveyResponse, Question, Choice, Answer
from .serializers import QuestionStatisticsSerializer

# ... (mavjud view'lar) ...


# --- YANGI STATISTIKA API ---

# auth_app/views.py
# ... (mavjud importlar)

class SurveyStatisticsAPIView(APIView):
    """
    Bitta so'rovnoma uchun barcha statistikani hisoblab,
    JSON formatida qaytaradigan API endpoint. Ma'lumotlar bazasidagi aniq ma'lumotlar bilan.
    """
    # Temporary comment out for testing
    # permission_classes = [IsAdminUser]

    def get(self, request, survey_pk):
        # Manual staff check
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"error": "Sizda bu API'ga kirish huquqi yo'q."}, status=403)
            
        try:
            survey = Survey.objects.get(pk=survey_pk)
        except Survey.DoesNotExist:
            return Response({"error": "So'rovnoma topilmadi."}, status=404)

        responses = SurveyResponse.objects.filter(survey=survey).select_related('student')
        
        total_participants = responses.count()
        
        # --- So'rovnoma haqida asosiy ma'lumotlar ---
        survey_info = {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "is_anonymous": survey.is_anonymous,
            "created_at": survey.created_at.strftime("%Y-%m-%d %H:%M:%S") if survey.created_at else None,
            "updated_at": survey.updated_at.strftime("%Y-%m-%d %H:%M:%S") if survey.updated_at else None,
            "is_active": survey.is_active,
            "questions_count": survey.questions.count(),
            "total_responses": total_participants,
        }
        
        # --- Demografik statistika ---
        faculty_stats, level_stats, gender_stats = {}, {}, {}
        education_form_stats, payment_form_stats = {}, {}

        if not survey.is_anonymous and total_participants > 0:
            faculty_stats = self._get_grouped_stats(responses, 'student__faculty_name_api', "Fakultet noma'lum")
            level_stats = self._get_grouped_stats(responses, 'student__level_name', "Kurs noma'lum")
            gender_stats = self._get_grouped_stats(responses, 'student__gender_name', "Jinsi noma'lum")
            education_form_stats = self._get_grouped_stats(responses, 'student__education_form_name', "Ta'lim shakli noma'lum")
            payment_form_stats = self._get_grouped_stats(responses, 'student__payment_form_name', "To'lov shakli noma'lum")
        
        # --- Javoblar bo'yicha batafsil ma'lumotlar ---
        responses_details = []
        if not survey.is_anonymous:
            for response in responses[:100]:  # Birinchi 100 ta javobni olamiz
                student = response.student
                response_detail = {
                    "response_id": response.id,
                    "submitted_at": response.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if response.submitted_at else None,
                    "student_info": {
                        "student_id_number": student.student_id_number,
                        "full_name": student.full_name,
                        "faculty": student.faculty_name_api,
                        "level": student.level_name,
                        "gender": student.gender_name,
                        "education_form": student.education_form_name,
                        "payment_form": student.payment_form_name,
                    } if student else None,
                    "answers_count": response.answers.count()
                }
                responses_details.append(response_detail)
        
        # --- Savollar bo'yicha statistika ---
        questions_stats_data = []
        questions = Question.objects.filter(survey=survey).prefetch_related('choices')

        for question in questions:
            question_data = {
                'id': question.id, 
                'text': question.text, 
                'question_type': question.question_type,
                'is_required': question.is_required,
                'order': question.order,
                'choices_stats': [], 
                'text_answers': [],
                'total_answers': 0
            }
            
            if question.question_type in ['single_choice', 'multiple_choice']:
                choices_with_counts = question.choices.annotate(
                    count=Count('chosen_in_answers', filter=Q(chosen_in_answers__survey_response__survey=survey)) +
                          Count('multi_chosen_in_answers', filter=Q(multi_chosen_in_answers__survey_response__survey=survey))
                ).order_by('-count')
                
                total_question_answers = sum(c.count for c in choices_with_counts)
                question_data['total_answers'] = total_question_answers
                
                for choice in choices_with_counts:
                    percentage = (choice.count / total_question_answers * 100) if total_question_answers > 0 else 0
                    question_data['choices_stats'].append({
                        "id": choice.id, 
                        "text": choice.text, 
                        "count": choice.count,
                        "percentage": round(percentage, 2)
                    })
                    
            elif question.question_type == 'text':
                text_answers = Answer.objects.filter(
                    survey_response__survey=survey, 
                    question=question
                ).exclude(text_answer__exact='').values_list('text_answer', flat=True)
                
                question_data['total_answers'] = text_answers.count()
                question_data['text_answers'] = list(text_answers[:50])  # Birinchi 50 ta matnli javob
                
            questions_stats_data.append(question_data)
        
        # --- Yakuniy JSON javobini yig'ish ---
        final_data = {
            "survey_info": survey_info,
            "total_participants": total_participants,
            "demographics": {
                "by_faculty": faculty_stats,
                "by_level": level_stats,
                "by_gender": gender_stats,
                "by_education_form": education_form_stats,
                "by_payment_form": payment_form_stats,
            },
            "responses_details": responses_details,
            "questions_statistics": questions_stats_data,
            "summary": {
                "total_questions": len(questions_stats_data),
                "completion_rate": round((total_participants / 1000) * 100, 2) if total_participants > 0 else 0,  # Taxminiy
                "average_responses_per_question": round(sum(q.get('total_answers', 0) for q in questions_stats_data) / len(questions_stats_data), 2) if questions_stats_data else 0
            }
        }
        
        return Response(final_data)

    def _get_grouped_stats(self, queryset, group_by_field, default_key="Noma'lum"):
        # ... (bu metod o'zgarishsiz qoladi)
        stats = queryset.values(group_by_field).annotate(count=Count('id')).order_by('-count')
        result = {}
        for item in stats:
            key = item[group_by_field] or default_key
            result[key] = item['count']
        return result

# auth_app/views.py
# ... mavjud importlar
from django.contrib.auth.decorators import user_passes_test

def is_staff_user(user):
    return user.is_staff

@user_passes_test(is_staff_user) # Faqat admin (staff) foydalanuvchilar kira oladi
@custom_login_required_with_token_refresh
def survey_statistics_view(request, survey_pk):
    """
    Bitta so'rovnomaning statistikasini ko'rsatadigan sahifani render qiladi.
    Asosiy ma'lumotlar JavaScript orqali API'dan olinadi.
    """
    # Faqat staff foydalanuvchilar kirishi mumkin
    if not request.user.is_staff:
        return HttpResponseForbidden("Sizda bu sahifaga kirish huquqi yo'q.")
    
    try:
        survey = Survey.objects.get(pk=survey_pk)
    except Survey.DoesNotExist:
        raise Http404("So'rovnoma topilmadi")
        
    context = {
        'survey': survey,
        'page_title': f'"{survey.title}" Statistikasi'
    }
    return render(request, 'auth_app/survey_stat.html', context)


from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ResponsiblePerson, MessageToResponsible, MessageReply
from .forms import MessageToResponsibleForm, MessageReplyForm

@method_decorator(custom_login_required_with_token_refresh, name="dispatch")
class ResponsiblePersonListView(ListView):
    """Mas'ul shaxslar ro'yxati — faqat autentifikatsiyalangan talaba (FIND-004)."""
    model = ResponsiblePerson
    template_name = "auth_app/responsible_list.html"
    context_object_name = "responsibles"
    queryset = ResponsiblePerson.objects.filter(is_active=True)

@custom_login_required_with_token_refresh
def message_list_view(request):
    """Xabarlar ro'yxati - function-based view"""
    # Admin foydalanuvchilar uchun barcha xabarlar
    if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
        messages_list = MessageToResponsible.objects.all().order_by('-created_at')
    else:
        # Oddiy foydalanuvchilar uchun faqat o'zlariga tegishli xabarlar
        student = getattr(request, 'current_student', None)
        if student:
            messages_list = MessageToResponsible.objects.filter(student=student).order_by('-created_at')
        else:
            messages_list = MessageToResponsible.objects.none()
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'messages': page_obj,
        'student': getattr(request, 'current_student', None),
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    
    return render(request, 'auth_app/message_list.html', context)

@custom_login_required_with_token_refresh
def message_detail_view(request, pk):
    """Xabar tafsilotlari - function-based view"""
    try:
        message = MessageToResponsible.objects.get(pk=pk)
        
        # Admin emas bo'lsa, faqat o'z xabarlarini ko'rish huquqi
        if not (hasattr(request.user, 'is_superuser') and request.user.is_superuser):
            student = getattr(request, 'current_student', None)
            if not student or message.student != student:
                messages.error(request, "Bu xabarni ko'rish huquqingiz yo'q.")
                return redirect('message_list')
        
        context = {
            'message': message,
            'student': getattr(request, 'current_student', None),
        }
        
        return render(request, 'auth_app/message_detail.html', context)
        
    except MessageToResponsible.DoesNotExist:
        messages.error(request, "Xabar topilmadi.")
        return redirect('message_list')

@method_decorator(staff_member_required, name="dispatch")
class MessageReplyView(CreateView):
    """
    Javob faqat staff/admin tomonidan — object-level: xabar mavjudligi tekshiriladi (FIND-008).
    """
    model = MessageReply
    form_class = MessageReplyForm
    template_name = "auth_app/message_reply_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.message_obj = get_object_or_404(MessageToResponsible, pk=kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.message = self.message_obj
        form.instance.replied_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("message_detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["message"] = self.message_obj
        return ctx


@method_decorator(custom_login_required_with_token_refresh, name="dispatch")
@method_decorator(
    rate_limit(
        'message_create',
        limit=getattr(settings, 'RATE_LIMIT_MESSAGE', 15),
        window_seconds=60,
        methods=('POST',),
    ),
    name="dispatch",
)
class MessageCreateView(CreateView):
    model = MessageToResponsible
    form_class = MessageToResponsibleForm
    template_name = "auth_app/message_create.html"
    success_url = reverse_lazy("message_list")

    def form_valid(self, form):
        student = getattr(self.request.user, 'student', None)
        if not student:
            student = getattr(self.request, 'current_student', None)
        if not student:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Talaba ma'lumotlari topilmadi. Iltimos, qayta kiring.")
        form.instance.student = student
        return super().form_valid(form)

# get_student_from_request funksiyasi o'chirildi - endi custom_login_required_with_token_refresh dekorator ishlatamiz