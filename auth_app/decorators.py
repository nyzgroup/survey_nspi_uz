from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import Student
from .utils import _handle_api_token_refresh

def custom_login_required_with_token_refresh(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        student_db_id_in_session = request.session.get('student_db_id')
        api_token_in_session = request.session.get('api_token')

        if not api_token_in_session or not student_db_id_in_session:
            messages.warning(request, "Iltimos, davom etish uchun tizimga kiring.")
            login_url_name = reverse('login')
            current_path = request.get_full_path()
            return redirect(f'{login_url_name}?next={current_path}')
        
        try:
            request.current_student = Student.objects.get(pk=student_db_id_in_session)
        except Student.DoesNotExist:
            request.session.flush()
            messages.error(request, "Sessiya yaroqsiz yoki foydalanuvchi topilmadi. Iltimos, qayta kiring.")
            return redirect(reverse('login'))

        if not _handle_api_token_refresh(request):
            return redirect(reverse('login'))
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view