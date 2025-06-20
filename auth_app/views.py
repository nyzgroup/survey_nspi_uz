# auth_app/views.py
import logging
from functools import wraps
from .decorators import custom_login_required_with_token_refresh
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.urls import reverse # reverse ni import qilish
from django.utils import timezone
from django.core.cache import cache
from django.http import Http404, HttpResponseForbidden

from .forms import LoginForm
from .models import Student,Survey, SurveyResponse, Answer, Question
from .services.hemis_api_service import HemisAPIClient, APIClientException
from .utils import map_api_data_to_student_model_defaults, update_student_instance_with_defaults # <--- YANGI IMPORTLAR



from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required # Yoki bizning custom_login_required
from .forms import create_answer_form_set # Yangi forma

logger = logging.getLogger(__name__)
REQUESTS_VERIFY_SSL = getattr(settings, 'REQUESTS_VERIFY_SSL', True)
API_TOKEN_REFRESH_THRESHOLD_SECONDS = getattr(settings, 'API_TOKEN_REFRESH_THRESHOLD_SECONDS', 5 * 60) # default 5 daqiqa

class AuthenticationFailed(APIClientException):
    pass

class PermissionDeniedAPI(APIClientException):
    pass

# --- Helper Functions ---
def _get_error_log_id():
    return timezone.now().strftime('%Y%m%d%H%M%S%f')

def _handle_api_token_refresh(request):
    refresh_cookie = request.session.get('hemis_refresh_cookie')
    current_token_expiry = request.session.get('api_token_expiry_timestamp')
    log_id_base = _get_error_log_id()

    needs_refresh = not current_token_expiry or \
                    current_token_expiry <= timezone.now().timestamp() + API_TOKEN_REFRESH_THRESHOLD_SECONDS

    if not refresh_cookie or not needs_refresh:
        return True

    logger.info(f"Attempting to refresh API token for session: {request.session.session_key}")
    api_client = HemisAPIClient() # Token bu yerda kerak emas, refresh_auth_token o'zi refresh_cookie ni ishlatadi
    log_id = f"{log_id_base}_REFRESH"

    try:
        new_access_token, new_refresh_cookie_data = api_client.refresh_auth_token(refresh_cookie)
        request.session['api_token'] = new_access_token
        
        # API javobidan 'expires_in' olishga harakat qilamiz
        expires_in = settings.SESSION_COOKIE_AGE # default
        if isinstance(new_refresh_cookie_data, dict) and 'expires_in' in new_refresh_cookie_data:
            try:
                expires_in = int(new_refresh_cookie_data['expires_in'])
            except (ValueError, TypeError):
                logger.warning(f"API dan kelgan 'expires_in' ({new_refresh_cookie_data['expires_in']}) yaroqsiz. Standart qiymat ishlatiladi.")
        
        request.session['api_token_expiry_timestamp'] = timezone.now().timestamp() + expires_in

        # Agar API yangi refresh cookie qaytarsa (string yoki dict ichida)
        new_actual_refresh_cookie = None
        if isinstance(new_refresh_cookie_data, str):
            new_actual_refresh_cookie = new_refresh_cookie_data
        elif isinstance(new_refresh_cookie_data, dict) and new_refresh_cookie_data.get('refresh_token_cookie_value'):
            new_actual_refresh_cookie = new_refresh_cookie_data['refresh_token_cookie_value']
        elif isinstance(new_refresh_cookie_data, dict) and new_refresh_cookie_data.get('refresh_cookie'): # Boshqa nom bilan kelishi mumkin
            new_actual_refresh_cookie = new_refresh_cookie_data['refresh_cookie']


        if new_actual_refresh_cookie:
            request.session['hemis_refresh_cookie'] = new_actual_refresh_cookie
            logger.info(f"Refresh cookie also updated for session: {request.session.session_key}")
        
        logger.info(f"API token successfully refreshed for session: {request.session.session_key}. New expiry: {timezone.datetime.fromtimestamp(request.session['api_token_expiry_timestamp'])}")
        return True
    except APIClientException as e:
        logger.error(f"Error Log ID: {log_id} - Failed to refresh API token: {e.args[0]} (Status: {e.status_code})", 
                     extra={'response_data': e.response_data, 'session_key': request.session.session_key})
        request.session.flush()
        messages.error(request, f"Sessiyangiz muddati tugadi. Iltimos, qayta kiring. (Xatolik ID: {log_id})")
        return False
    except Exception as e:
        logger.critical(f"Error Log ID: {log_id} - Unexpected error during token refresh: {e}", 
                        exc_info=True, extra={'session_key': request.session.session_key})
        request.session.flush()
        messages.error(request, f"Tokenni yangilashda kutilmagan xatolik. Qayta kiring. (Xatolik ID: {log_id})")
        return False

# --- Decorators ---
def custom_login_required_with_token_refresh(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        student_db_id_in_session = request.session.get('student_db_id')
        api_token_in_session = request.session.get('api_token')

        if not api_token_in_session or not student_db_id_in_session:
            messages.warning(request, "Iltimos, davom etish uchun tizimga kiring.")
            login_url_name = settings.LOGIN_URL # Bu odatda URL nomi bo'ladi
            try:
                login_url_path = reverse(login_url_name)
            except Exception:
                login_url_path = f"/{login_url_name}/" # Fallback agar reverse ishlamasa
            
            current_path = request.get_full_path()
            return redirect(f'{login_url_path}?next={current_path}')
        
        try:
            request.current_student = Student.objects.get(pk=student_db_id_in_session)
        except Student.DoesNotExist:
            logger.warning(f"Student ID {student_db_id_in_session} from session not found in DB. Flushing session.")
            request.session.flush()
            messages.error(request, "Sessiya yaroqsiz yoki foydalanuvchi topilmadi. Iltimos, qayta kiring.")
            return redirect(settings.LOGIN_URL) # LOGIN_URL bu yerda ham nom bo'lishi kerak

        if not _handle_api_token_refresh(request):
            # _handle_api_token_refresh xabar berib, sessiyani tozalab, False qaytaradi.
            # Login sahifasiga redirect kerak.
            return redirect(settings.LOGIN_URL)
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# --- Views ---
def login_view(request):
    if 'api_token' in request.session and 'student_db_id' in request.session:
        if _handle_api_token_refresh(request):
            try:
                # Foydalanuvchi hali ham bazada mavjudligini tekshirish
                Student.objects.get(pk=request.session['student_db_id'])
                next_url = request.session.pop('login_next_url', None) or request.GET.get('next')
                return redirect(next_url or 'dashboard')
            except Student.DoesNotExist:
                logger.warning(f"Logged in user (ID: {request.session.get('student_db_id')}) not found in DB. Flushing session.")
                request.session.flush()
                # Bu holatda login formaga qaytamiz
        else:
            # Token yangilash muvaffaqiyatsiz bo'lsa, _handle_api_token_refresh o'zi login sahifasiga
            # yo'naltirishi yoki xabar berishi kerak. Agar yo'naltirmasa, bu yerda:
            return redirect(settings.LOGIN_URL)


    if request.method == 'GET' and 'next' in request.GET:
        request.session['login_next_url'] = request.GET.get('next')

    form = LoginForm(request.POST or None)
    log_id_base = _get_error_log_id()

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        api_client = HemisAPIClient()

        try:
            logger.info(f"Login attempt for user: {username}")
            api_token, refresh_data = api_client.login(username, password) # refresh_data endi dict yoki string bo'lishi mumkin
            
            logger.info(f"Login successful for {username}, fetching account data with new token.")
            student_info_from_api = api_client.get_account_me(api_token_override=api_token)

            if not student_info_from_api or not isinstance(student_info_from_api, dict):
                log_id = f"{log_id_base}_NODATA"
                logger.error(f"Error Log ID: {log_id} - No student data received from API for {username} or data is not a dict. API Response: {str(student_info_from_api)[:250]}")
                messages.error(request, f"API dan ma'lumot olishda xatolik. (Xatolik ID: {log_id})")
                return render(request, 'auth_app/login.html', {'form': form})

            with transaction.atomic():
                student_defaults = map_api_data_to_student_model_defaults(student_info_from_api, username)
                if not student_defaults: # Agar map_api_data_to_student_model_defaults bo'sh qaytarsa
                    raise ValueError("API ma'lumotlarini modellashtirishda xatolik.")

                student, created = Student.objects.update_or_create(
                    username=username,
                    defaults=student_defaults # update_or_create o'zi o'zgarishlarni saqlaydi
                )
            
            request.session['api_token'] = api_token
            request.session['student_db_id'] = student.id
            request.session['username_display'] = str(student)
            
            expires_in_login = settings.SESSION_COOKIE_AGE # default
            refresh_cookie_login = None

            if isinstance(refresh_data, str): # Agar refresh_data to'g'ridan-to'g'ri cookie string bo'lsa
                refresh_cookie_login = refresh_data
            elif isinstance(refresh_data, dict):
                if 'expires_in' in refresh_data:
                    try:
                        expires_in_login = int(refresh_data['expires_in'])
                    except (ValueError, TypeError):
                        logger.warning(f"Login API dan kelgan 'expires_in' ({refresh_data['expires_in']}) yaroqsiz.")
                
                if 'refresh_token_cookie_value' in refresh_data:
                    refresh_cookie_login = refresh_data['refresh_token_cookie_value']
                elif 'refresh_cookie' in refresh_data: # Boshqa nom bilan
                    refresh_cookie_login = refresh_data['refresh_cookie']
                # Agar refresh token to'g'ridan-to'g'ri 'refresh_token' kaliti bilan kelsa:
                # elif 'refresh_token' in refresh_data: 
                #    request.session['hemis_refresh_token_value'] = refresh_data['refresh_token'] # Buni saqlash kerak bo'lsa
            
            request.session['api_token_expiry_timestamp'] = timezone.now().timestamp() + expires_in_login
            
            if refresh_cookie_login:
                request.session['hemis_refresh_cookie'] = refresh_cookie_login
            
            request.session.set_expiry(settings.SESSION_COOKIE_AGE) # Django sessiyasining muddati

            display_name = student_defaults.get('full_name_api') or student.username
            messages.success(request, f"Xush kelibsiz, {display_name}!")
            logger.info(f"User {username} logged in. Session expiry: {request.session.get_expiry_date()}, API token expiry: {timezone.datetime.fromtimestamp(request.session['api_token_expiry_timestamp'])}")
            
            next_url = request.session.pop('login_next_url', None) or request.GET.get('next')
            return redirect(next_url or 'dashboard')

        except APIClientException as e:
            log_id = f"{log_id_base}_APICLI"
            logger.error(
                f"Error Log ID: {log_id} - User: {username}, APIClientException: {e.args[0]}, "
                f"Status: {e.status_code}, API Response: {str(e.response_data)[:250]}, URL: {e.url}",
                exc_info=False
            )
            user_message = str(e.args[0] if e.args else "Noma'lum API xatosi")
            if e.status_code in [400, 401, 403] or \
               (isinstance(user_message, str) and any(term in user_message.lower() for term in ["token", "authentication", "авторизации", "credentials", "login", "parol", "not found", "no active account"])):
                 user_message = "Login yoki parol xato."
            elif e.status_code == 503 or (e.status_code is None and any(term in user_message.lower() for term in ["connection", "ulan", "refused"])):
                user_message = "API serveriga ulanib bo'lmadi. Internet aloqangizni tekshiring yoki keyinroq urinib ko'ring."
            elif e.status_code == 504 or (e.status_code is None and "timeout" in user_message.lower()):
                user_message = "API serveridan javob kutish vaqti tugadi."
            elif e.status_code == 404 and e.url and "/auth/login" in str(e.url):
                 user_message = "Autentifikatsiya xizmati manzili noto'g'ri sozlanган."
            elif not user_message or user_message == "Noma'lum API xatosi":
                 user_message = "API bilan bog'lanishda noma'lum xatolik."

            messages.error(request, f"{user_message} (Xatolik ID: {log_id})")
        
        except ValueError as ve: # Masalan, map_api_data_to_student_model_defaults xatolik qaytarsa
            log_id = f"{log_id_base}_VALERR"
            logger.error(f"Error Log ID: {log_id} - User: {username}, ValueError: {ve}", exc_info=True)
            messages.error(request, f"Ma'lumotlarni qayta ishlashda xatolik. (Xatolik ID: {log_id})")

        except Exception as e:
            log_id = f"{log_id_base}_UNEXP"
            logger.critical(f"Error Log ID: {log_id} - User: {username}, Unexpected error in login_view: {type(e).__name__} - {e}", exc_info=True)
            messages.error(request, f"Noma'lum tizim xatoligi yuz berdi. Iltimos, administratorga murojaat qiling. (Xatolik ID: {log_id})")

    context = {'form': form}
    return render(request, 'auth_app/login.html', context)


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
    if 'api_token' in request.session and 'student_db_id' in request.session:
        if _handle_api_token_refresh(request):
            return redirect('dashboard')
        else:
            return redirect(settings.LOGIN_URL)
    # Agar LOGIN_URL 'login' bo'lsa, templates/home.html ni render qilish o'rniga
    # to'g'ridan-to'g'ri login sahifasiga yo'naltirish mumkin.
    # return redirect(settings.LOGIN_URL)
    return render(request, 'auth_app/home.html')


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


    context = {
        'student': current_student, # Endi bu yangilangan bo'lishi mumkin
        'username_display': str(current_student),
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
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_protect

# --- Mahalliy (local) importlar ---
from .decorators import custom_login_required_with_token_refresh
from .forms import LoginForm, create_answer_form_set
from .models import Student, Survey, SurveyResponse, Answer, Question
from .services.hemis_api_service import HemisAPIClient, APIClientException
from .utils import map_api_data_to_student_model_defaults, update_student_instance_with_defaults

logger = logging.getLogger(__name__)

# ... (login_view, logout_view, dashboard_view, survey_list_view va boshqa funksiyalar bu yerda) ...
# Biz faqat survey_detail_view va yangi API view'ni o'zgartiramiz.


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
        'survey_data_json': mark_safe(json.dumps(survey_data, ensure_ascii=False)),
        'csrf_token': get_token(request),  # CSRF tokenini to'g'ridan-to'g'ri uzatish
        'student': student,
        'username_display': str(student),
    }
    return render(request, 'auth_app/survey_detail.html', context)


@csrf_protect  # CSRF himoyasini qo'lda ta'minlaydi
@custom_login_required_with_token_refresh
def submit_survey_api_view(request, survey_pk):
    """
    JavaScript'dan AJAX/Fetch orqali kelgan JSON javoblarni qabul qiladigan API endpoint.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Faqat POST so\'rovlariga ruxsat etilgan.'}, status=405)

    survey = get_object_or_404(Survey, pk=survey_pk)
    student = request.current_student

    # Qayta ishtirok etishni tekshirish (poyga holatlari uchun muhim)
    if not survey.is_anonymous and SurveyResponse.objects.filter(survey=survey, student=student).exists():
        return JsonResponse({'status': 'error', 'message': 'Siz bu so\'rovnomada avval qatnashgansiz.'}, status=400)

    try:
        data = json.loads(request.body)
        answers_data = data.get('answers', {})

        # Hech bo'lmasa bitta javob borligini tekshirish
        if not answers_data or not any(answers_data.values()):
             return JsonResponse({'status': 'error', 'message': 'Iltimos, kamida bitta savolga javob bering.'}, status=400)

        with transaction.atomic():
            survey_response = SurveyResponse.objects.create(
                survey=survey,
                student=student if not survey.is_anonymous else None
            )

            # Savollarni oldindan lug'atga yuklab olish (har bir iteratsiyada DB so'rovi qilmaslik uchun)
            questions_map = {q.id: q for q in survey.questions.all()}

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
                    answer.selected_choice_id = int(value)
                    answer.save()
                elif question.question_type == 'multiple_choice' and isinstance(value, list):
                    answer.save()  # M2M bog'lanishidan oldin asosiy obyekt saqlanishi shart
                    choice_ids = [int(cid) for cid in value]
                    answer.selected_choices.set(choice_ids)
        
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
    JSON formatida qaytaradigan API endpoint. YANGILANGAN.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, survey_pk):
        try:
            survey = Survey.objects.get(pk=survey_pk)
        except Survey.DoesNotExist:
            return Response({"error": "So'rovnoma topilmadi."}, status=404)

        responses = SurveyResponse.objects.filter(survey=survey).select_related('student')
        
        total_participants = responses.count()
        
        # --- Demografik statistika ---
        # Yangi kesimlar qo'shildi
        faculty_stats, level_stats, gender_stats = {}, {}, {}
        education_form_stats, payment_form_stats = {}, {}
        social_category_stats, accommodation_stats = {}, {}

        if not survey.is_anonymous and total_participants > 0:
            faculty_stats = self._get_grouped_stats(responses, 'student__faculty_name_api', "Fakultet noma'lum")
            level_stats = self._get_grouped_stats(responses, 'student__level_name', "Kurs noma'lum")
            gender_stats = self._get_grouped_stats(responses, 'student__gender_name', "Jinsi noma'lum")
            education_form_stats = self._get_grouped_stats(responses, 'student__education_form_name', "Ta'lim shakli noma'lum")
            payment_form_stats = self._get_grouped_stats(responses, 'student__payment_form_name', "To'lov shakli noma'lum")
            social_category_stats = self._get_grouped_stats(responses, 'student__social_category_name', "Ijtimoiy holat noma'lum")
            accommodation_stats = self._get_grouped_stats(responses, 'student__accommodation_name', "Turar joyi noma'lum")
        
        # --- Savollar bo'yicha statistika ---
        questions_stats_data = []
        questions = Question.objects.filter(survey=survey).prefetch_related('choices')

        for question in questions:
            # ... (bu qism o'zgarishsiz qoladi, oldingi javobdagi kod) ...
            question_data = {'id': question.id, 'text': question.text, 'question_type': question.question_type, 'choices_stats': [], 'text_answers': []}
            if question.question_type in ['single_choice', 'multiple_choice']:
                choices_with_counts = question.choices.annotate(
                    count=Count('chosen_in_answers', filter=Q(chosen_in_answers__survey_response__survey=survey)) +
                          Count('multi_chosen_in_answers', filter=Q(multi_chosen_in_answers__survey_response__survey=survey))
                ).order_by('-count')
                question_data['choices_stats'] = [{"id": c.id, "text": c.text, "count": c.count} for c in choices_with_counts]
            elif question.question_type == 'text':
                text_answers = Answer.objects.filter(survey_response__survey=survey, question=question).values_list('text_answer', flat=True).exclude(text_answer__exact='')
                question_data['text_answers'] = list(text_answers[:50])
            questions_stats_data.append(question_data)
        
        # --- Yakuniy JSON javobini yig'ish ---
        final_data = {
            "survey_title": survey.title,
            "total_participants": total_participants,
            "demographics": {
                "by_faculty": faculty_stats,
                "by_level": level_stats,
                "by_gender": gender_stats,
                "by_education_form": education_form_stats,
                "by_payment_form": payment_form_stats,
                "by_social_category": social_category_stats,
                "by_accommodation": accommodation_stats,
            },
            "questions_statistics": questions_stats_data
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
def survey_statistics_view(request, survey_pk):
    """
    Bitta so'rovnomaning statistikasini ko'rsatadigan sahifani render qiladi.
    Asosiy ma'lumotlar JavaScript orqali API'dan olinadi.
    """
    try:
        survey = Survey.objects.get(pk=survey_pk)
    except Survey.DoesNotExist:
        raise Http404("So'rovnoma topilmadi")
        
    context = {
        'survey': survey,
        'page_title': f'"{survey.title}" Statistikasi'
    }
    return render(request, 'auth_app/survey_stat.html', context)