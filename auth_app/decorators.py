from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import Student, Employee
from .utils import _handle_api_token_refresh


def custom_login_required_with_token_refresh(view_func):
    """Talaba sessiyasini tekshiradi. Hodim sessiyasi bo'lsa — employee_home ga yo'naltiradi."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_token        = request.session.get('api_token')
        student_db_id    = request.session.get('student_db_id')
        employee_db_id   = request.session.get('employee_db_id')
        login_url        = reverse('login')
        current_path     = request.get_full_path()

        # Hodim sessiyasi bor bo'lsa — hodim sahifasiga yo'naltiriladi
        if api_token and employee_db_id:
            return redirect(reverse('employee_home'))

        if not (api_token and student_db_id):
            messages.warning(request, "Iltimos, davom etish uchun tizimga kiring.")
            return redirect(f'{login_url}?next={current_path}')

        try:
            request.current_student  = Student.objects.get(pk=student_db_id)
            request.current_employee = None
        except Student.DoesNotExist:
            request.session.flush()
            messages.error(request, "Sessiya yaroqsiz yoki foydalanuvchi topilmadi. Iltimos, qayta kiring.")
            return redirect(login_url)

        if not _handle_api_token_refresh(request):
            return redirect(login_url)

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employee_login_required(view_func):
    """Hodim sessiyasini tekshiradi. Talaba sessiyasi bo'lsa — dashboard ga yo'naltiradi."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_token      = request.session.get('api_token')
        employee_db_id = request.session.get('employee_db_id')
        student_db_id  = request.session.get('student_db_id')
        login_url      = reverse('login')
        current_path   = request.get_full_path()

        # Talaba sessiyasi bor bo'lsa — dashboard ga yo'naltiriladi
        if api_token and student_db_id:
            return redirect(reverse('dashboard'))

        if not (api_token and employee_db_id):
            messages.warning(request, "Iltimos, davom etish uchun tizimga kiring.")
            return redirect(f'{login_url}?next={current_path}')

        try:
            request.current_employee = Employee.objects.get(pk=employee_db_id)
            request.current_student  = None
        except Employee.DoesNotExist:
            request.session.flush()
            messages.error(request, "Sessiya yaroqsiz yoki foydalanuvchi topilmadi. Iltimos, qayta kiring.")
            return redirect(login_url)

        return view_func(request, *args, **kwargs)
    return _wrapped_view
