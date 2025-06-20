from django.contrib import admin, messages
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.db.models import Count
import logging
import os
from .models import (
    Student, Survey, SurveyFile, Question, Choice, SurveyResponse, Answer,
    ResponsiblePerson, MessageToResponsible, MessageAttachment
)
logger = logging.getLogger(__name__)
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 1000
    list_display = (
        'username', 'student_id_number', 'api_user_hash',
        'first_name', 'last_name', 'patronymic', 'full_name_api', 'short_name_api',
        'get_image_preview', 'birth_date_timestamp', 'passport_pin', 'passport_number', 'email', 'phone',
        'gender_code', 'gender_name', 'university_name_api',
        'specialty_id_api', 'specialty_code_api', 'specialty_name_api',
        'student_status_code', 'student_status_name',
        'education_form_code', 'education_form_name',
        'education_type_code', 'education_type_name',
        'payment_form_code', 'payment_form_name',
        'group_id_api', 'group_name_api', 'group_education_lang_code', 'group_education_lang_name',
        'faculty_id_api', 'faculty_name_api', 'faculty_code_api',
        'education_lang_code', 'education_lang_name',
        'level_code', 'level_name',
        'semester_id_api', 'semester_code_api', 'semester_name_api', 'semester_is_current',
        'semester_education_year_code', 'semester_education_year_name', 'semester_education_year_is_current',
        'avg_gpa', 'password_is_valid_api', 'address_api',
        'country_code_api', 'country_name_api',
        'province_code_api', 'province_name_api',
        'district_code_api', 'district_name_api',
        'social_category_code', 'social_category_name',
        'accommodation_code', 'accommodation_name',
        'validate_url_api', 'last_login_api', 'created_at', 'updated_at'
    )
    list_filter = (
        'faculty_name_api', 
        'level_name', 
        'education_form_name', 
        'student_status_name',
        'last_login_api',
        'updated_at',
        'created_at'
    )
    search_fields = (
        'username', 
        'first_name', 
        'last_name', 
        'student_id_number', 
        'full_name_api',
        'faculty_name_api', 
        'group_name_api',
        'email',
        'phone'
    )
    ordering = ('-updated_at', 'last_name', 'first_name')
    readonly_fields_list = [
        'username', 'student_id_number', 'api_user_hash',
        'first_name', 'last_name', 'patronymic', 'full_name_api', 'short_name_api',
        'get_image_preview',
        'birth_date_timestamp', 'get_birth_date_display_admin',
        'passport_pin', 'passport_number', 'email', 'phone', 
        'gender_code', 'gender_name', 'university_name_api',
        'specialty_id_api', 'specialty_code_api', 'specialty_name_api',
        'student_status_code', 'student_status_name', 'education_form_code',
        'education_form_name', 'education_type_code', 'education_type_name',
        'payment_form_code', 'payment_form_name', 'group_id_api', 'group_name_api',
        'group_education_lang_code', 'group_education_lang_name', 'faculty_id_api',
        'faculty_name_api', 'faculty_code_api', 'education_lang_code',
        'education_lang_name', 'level_code', 'level_name', 'semester_id_api',
        'semester_code_api', 'semester_name_api', 'semester_is_current',
        'semester_education_year_code', 'semester_education_year_name',
        'semester_education_year_is_current', 'avg_gpa', 'password_is_valid_api',
        'address_api', 'country_code_api', 'country_name_api', 'province_code_api',
        'province_name_api', 'district_code_api', 'district_name_api',
        'social_category_code', 'social_category_name', 'accommodation_code',
        'accommodation_name', 'validate_url_api', 
        'last_login_api_formatted_detail',
        'created_at_formatted_detail', 
        'updated_at_formatted_detail'
    ]
    readonly_fields = tuple(readonly_fields_list)

    fieldsets = (
        ('Asosiy Login Ma\'lumotlari', {
            'fields': ('username', 'student_id_number', 'api_user_hash')
        }),
        ('Shaxsiy Ma\'lumotlar (API)', {
            'fields': (
                'get_image_preview', 
                ('full_name_api', 'short_name_api'), 
                ('first_name', 'last_name', 'patronymic'),
                ('birth_date_timestamp', 'get_birth_date_display_admin'),
                'gender_name', 
                ('passport_pin', 'passport_number'), 
                'email', 'phone', 'address_api'
            )
        }),
        ('Universitet Ma\'lumotlari (API)', {
            'fields': (
                'university_name_api', 
                ('faculty_name_api', 'faculty_code_api'),
                ('specialty_name_api', 'specialty_code_api'), 
                'education_type_name', 'education_form_name',
                'education_lang_name', 'level_name', 
                ('group_name_api', 'group_education_lang_name'),
                ('semester_name_api', 'semester_is_current', 'semester_education_year_name'),
                'payment_form_name', 'student_status_name', 'avg_gpa', 
                'password_is_valid_api'
            )
        }),
        ('Manzil va Ijtimoiy Holat (API)', {
            'fields': (
                'country_name_api', 'province_name_api', 'district_name_api',
                'social_category_name', 'accommodation_name'
            )
        }),
        ('Tizim Ma\'lumotlari', {
            'fields': (
                'last_login_api_formatted_detail', 
                ('created_at_formatted_detail', 'updated_at_formatted_detail'), 
                'validate_url_api_link'
            ),
            'classes': ('collapse',),
        }),
    )

    def _format_datetime_for_admin(self, dt_value):
        if dt_value:
            local_tz = timezone.get_current_timezone()
            return timezone.localtime(dt_value, local_tz).strftime('%d-%m-%Y %H:%M:%S')
        return "Noma'lum"

    @admin.display(description='Oxirgi Kirish (API)', ordering='last_login_api')
    def last_login_api_formatted(self, obj):
        return self._format_datetime_for_admin(obj.last_login_api)
    
    @admin.display(description='Oxirgi Kirish (API)')
    def last_login_api_formatted_detail(self, obj):
        return self._format_datetime_for_admin(obj.last_login_api)

    @admin.display(description='Yaratilgan Vaqti')
    def created_at_formatted_detail(self, obj):
        return self._format_datetime_for_admin(obj.created_at)

    @admin.display(description='Yangilangan Vaqti', ordering='updated_at')
    def updated_at_formatted(self, obj):
        return self._format_datetime_for_admin(obj.updated_at)

    @admin.display(description='Yangilangan Vaqti')
    def updated_at_formatted_detail(self, obj):
        return self._format_datetime_for_admin(obj.updated_at)

    @admin.display(description='To\'liq F.I.Sh.', ordering='last_name')
    def get_full_name_display(self, obj):
        return obj.full_name_api or f"{obj.last_name or ''} {obj.first_name or ''}".strip() or obj.username

    @admin.display(description='Talabning surati ', empty_value="-Rasm yo'q-")
    def get_image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px; border-radius: 5px;" />', obj.image_url)
        return self.get_image_preview.empty_value
    
    @admin.display(description='Tug\'ilgan sana (Formatlangan)', ordering='birth_date_timestamp')
    def get_birth_date_display_admin(self, obj):
        if obj.birth_date_timestamp:
            try:
                dt_object = timezone.datetime.fromtimestamp(obj.birth_date_timestamp, tz=timezone.get_current_timezone())
                return dt_object.strftime('%d-%m-%Y')
            except (ValueError, TypeError, OSError):
                return "Noma'lum sana (xato)"
        return "-"


    @admin.display(description='API Validatsiya Havolasi')
    def validate_url_api_link(self, obj):
        if obj.validate_url_api:
            return format_html('<a href="{0}" target="_blank">Havola</a>', obj.validate_url_api)
        return "-"

    @admin.display(description='Profil To\'liqligi', boolean=True)
    def is_profile_complete(self, obj):
        required_fields = [
            obj.first_name, obj.last_name, 
            obj.student_id_number,
            obj.faculty_name_api, obj.level_name
        ]
        return all(field is not None and str(field).strip() != '' for field in required_fields)

    actions = ['refresh_selected_students_data_from_api_action']

    @admin.action(description="Tanlangan talabalar ma'lumotlarini API dan yangilash")
    def refresh_selected_students_data_from_api_action(self, request, queryset):
        admin_api_token = getattr(settings, 'HEMIS_ADMIN_API_TOKEN', None)        
        if not admin_api_token:
            self.message_user(request, "Ma'muriy API tokeni (HEMIS_ADMIN_API_TOKEN) sozlanmalarda topilmadi.", messages.ERROR)
            return
        
        updated_count = 0
        failed_students_info = []

        if updated_count > 0:
            self.message_user(request, f"{updated_count} ta talaba ma'lumotlari muvaffaqiyatli yangilandi.", messages.SUCCESS)
        elif queryset.exists():
             self.message_user(request, "Talaba ma'lumotlarini yangilash funksiyasi to'liq sozlanmagan yoki xatolik yuz berdi.", messages.WARNING)
        else:
            self.message_user(request, "Yangilash uchun talabalar tanlanmadi.", messages.INFO)


class SurveyFileInline(admin.TabularInline):
    list_per_page = 20
    list_max_show_all = 1000
    model = SurveyFile
    extra = 1
    fields = ('file', 'caption')
    readonly_fields = ('uploaded_at',)
    verbose_name = "So'rovnoma fayli"
    verbose_name_plural = "So'rovnoma fayllari"

class ChoiceInline(admin.TabularInline):
    list_per_page = 20
    list_max_show_all = 1000
    model = Choice
    extra = 3
    fields = ('text',)
    verbose_name = "Variant"
    verbose_name_plural = "Variantlar"

class QuestionInline(admin.StackedInline):
    list_per_page = 20
    list_max_show_all = 1000
    model = Question
    extra = 2
    fields = ('text', 'question_type', 'order', 'is_required')
    inlines = [ChoiceInline]
    show_change_link = True
    verbose_name = "Savol"
    verbose_name_plural = "Savollar to'plami"

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 1000
    list_display = ('title', 'start_date_formatted', 'end_date_formatted', 'is_active', 'is_anonymous', 'total_responses_link', 'created_by_admin_display', 'is_currently_open')
    list_filter = ('is_active', 'is_anonymous', 'start_date', 'end_date', 'created_by')
    search_fields = ('title', 'purpose', 'description', 'created_by__username')
    inlines = [SurveyFileInline, QuestionInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'purpose', 'description')
        }),
        ('Muddati va Holati', {
            'fields': (('start_date', 'end_date'), ('is_active', 'is_anonymous'))
        }),
        ('Tizim Ma\'lumotlari', {
            'fields': ('created_by_admin_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'created_by_admin_display')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if not obj.created_by_id:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Boshlanish sanasi')
    def start_date_formatted(self, obj):
        return obj.start_date.strftime('%Y-%m-%d %H:%M') if obj.start_date else '-'

    @admin.display(description='Tugash sanasi')
    def end_date_formatted(self, obj):
        return obj.end_date.strftime('%Y-%m-%d %H:%M') if obj.end_date else 'Muddatsiz'
    
    @admin.display(description='Yaratuvchi (Admin)')
    def created_by_admin_display(self, obj): # Hem list_display, hem readonly_fields uchun
        return obj.created_by.username if obj.created_by else 'Noma\'lum'

    @admin.display(description='Javoblar soni')
    def total_responses_link(self, obj):
        count = obj.responses_count # get_queryset dagi annotate dan
        if count > 0:
            url = (
                reverse("admin:auth_app_surveyresponse_changelist")
                + f"?survey__id__exact={obj.pk}"
            )
            return format_html('<a href="{}">{} ta javob</a>', url, count)
        return "0 ta javob"
    total_responses_link.admin_order_field = 'responses_count'

    @admin.display(description='Hozir ochiqmi?', boolean=True)
    def is_currently_open(self, obj):
        return obj.is_open

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(responses_count=Count('responses', distinct=True)) # distinct=True qo'shildi
        return qs

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 1000
    list_display = ('text_short', 'survey_link', 'question_type', 'order', 'is_required')
    list_filter = ('survey__title', 'question_type', 'is_required')
    search_fields = ('text', 'survey__title')
    inlines = [ChoiceInline]
    list_editable = ('order', 'is_required', 'question_type')
    list_display_links = ('text_short',)
    ordering = ('survey__title', 'order')

    fieldsets = (
        (None, {
            'fields': ('survey', 'text', 'question_type', 'order', 'is_required')
        }),
    )

    @admin.display(description='Savol matni (qisqa)')
    def text_short(self, obj):
        return obj.text[:70] + '...' if len(obj.text) > 70 else obj.text

    @admin.display(description='So\'rovnoma')
    def survey_link(self, obj):
        url = reverse("admin:auth_app_survey_change", args=[obj.survey.pk])
        return format_html('<a href="{}">{}</a>', url, obj.survey.title)

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 1000
    list_display = ('survey_title', 'student_name_display', 'submitted_at_formatted', 'view_answers_link')
    list_filter = ('survey__title', ('student', admin.RelatedOnlyFieldListFilter), 'submitted_at') # Studentni qidirish uchun
    search_fields = ('survey__title', 'student__username', 'student__first_name', 'student__last_name')
    readonly_fields = ('survey', 'student', 'submitted_at', 'answers_inline_display')

    fieldsets = (
        (None, {
            'fields': ('survey', 'student', 'submitted_at')
        }),
        ('Berilgan Javoblar', {
            'fields': ('answers_inline_display',),
            'classes': ('collapse', 'wide') # Kengroq ko'rinish
        }),
    )

    @admin.display(description='So\'rovnoma')
    def survey_title(self, obj):
        return obj.survey.title

    @admin.display(description='Talaba')
    def student_name_display(self, obj):
        if obj.survey.is_anonymous:
            return "Anonim"
        return str(obj.student) if obj.student else "Noma'lum"

    @admin.display(description='Yuborilgan vaqti')
    def submitted_at_formatted(self, obj):
        return obj.submitted_at.strftime('%Y-%m-%d %H:%M')

    @admin.display(description='Javoblarni ko\'rish')
    def view_answers_link(self, obj):
        url = reverse("admin:auth_app_surveyresponse_change", args=[obj.pk])
        return format_html('<a href="{}">Batafsil</a>', url)

    @admin.display(description='Berilgan Javoblar')
    def answers_inline_display(self, obj):
        answers_html = "<ul style='list-style-type: none; padding-left: 0;'>"
        for answer in obj.answers.all().select_related('question', 'selected_choice').prefetch_related('selected_choices'):
            answers_html += f"<li style='margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;'><strong>{answer.question.text}:</strong><br/>"
            if answer.question.question_type == 'text':
                if answer.text_answer:
                    answers_html += f"<div style='padding-left:15px;'>{mark_safe(answer.text_answer)}</div>"
                else:
                    answers_html += "<div style='padding-left:15px;'><i>Bo'sh</i></div>"
            elif answer.question.question_type == 'multiple_choice':
                choices_text = ", ".join([choice.text for choice in answer.selected_choices.all()])
                answers_html += f"<div style='padding-left:15px;'>[{choices_text if choices_text else '<i>Tanlanmagan</i>'}]</div>"
            elif answer.question.question_type == 'single_choice' and answer.selected_choice:
                answers_html += f"<div style='padding-left:15px;'>{answer.selected_choice.text}</div>"
            else:
                answers_html += "<div style='padding-left:15px;'><i>Javob topilmadi yoki noma'lum tur</i></div>"
            answers_html += "</li>"
        answers_html += "</ul>"
        return mark_safe(answers_html)
    
    def has_add_permission(self, request):
        return False
    # def has_change_permission(self, request, obj=None):
    #     return False # Agar umuman o'zgartirishni taqiqlamoqchi bo'lsangiz

@admin.register(ResponsiblePerson)
class ResponsiblePersonAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_max_show_all = 1000
    list_display = ('full_name', 'position', 'email', 'phone_number', 'is_active', 'received_messages_count')
    list_filter = ('is_active', 'position')
    search_fields = ('first_name', 'last_name', 'patronymic', 'position', 'email')
    fieldsets = (
        (None, {
            'fields': (('first_name', 'last_name', 'patronymic'), 'position', 'is_active')
        }),
        ('Aloqa Ma\'lumotlari', {
            'fields': ('email', 'phone_number', 'office_location'),
            'classes': ('collapse',)
        }),
        ('Mas\'uliyat Sohalari', {
            'fields': ('responsibilities_short',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Kelgan xabarlar')
    def received_messages_count(self, obj):
        count = obj.received_messages_from_students.count()
        if count > 0:
            url = (
                reverse("admin:auth_app_messagetoresponsible_changelist")
                + f"?responsible_person__id__exact={obj.pk}"
            )
            return format_html('<a href="{}">{} ta</a>', url, count)
        return "0 ta"
    received_messages_count.admin_order_field = 'messages_count' # get_queryset da annotate qilish kerak

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(messages_count=Count('received_messages_from_students', distinct=True))
        return qs


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    fields = ('file_link', 'original_filename', 'file_size_display', 'uploaded_at_formatted')
    readonly_fields = ('file_link', 'original_filename', 'file_size_display', 'uploaded_at_formatted')
    verbose_name = "Biriktirma"
    verbose_name_plural = "Biriktirmalar"
    
    @admin.display(description='Fayl')
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.file.url, obj.original_filename or "Fayl")
        return "-"
        
    @admin.display(description='Hajmi (KB)')
    def file_size_display(self, obj):
        return obj.file_size_kb
        
    @admin.display(description='Yuklangan vaqti')
    def uploaded_at_formatted(self, obj):
        return obj.uploaded_at.strftime('%Y-%m-%d %H:%M') if obj.uploaded_at else '-'

    def has_add_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(MessageToResponsible)
class MessageToResponsibleAdmin(admin.ModelAdmin):
    list_display = ('subject_short', 'student_link', 'responsible_person_link', 'status', 'created_at_formatted', 'responded_at_formatted', 'has_attachments')
    list_filter = ('status', 'responsible_person', 'created_at')
    search_fields = ('subject', 'content', 'student__username', 'student__first_name', 'student__last_name', 'responsible_person__first_name', 'responsible_person__last_name')
    list_editable = ('status',)
    readonly_fields = ('student', 'responsible_person', 'subject', 'content', 'created_at', 'updated_at', 'responded_by_display', 'responded_at')
    inlines = [MessageAttachmentInline]

    fieldsets = (
        ('Xabar Ma\'lumotlari', {
            'fields': ('student', 'responsible_person', 'subject', 'status', 'created_at', 'updated_at')
        }),
        ('Xabar Mazmuni', { # Content ni alohida fieldsetga olish mumkin
            'fields': ('content',),
            'classes': ('wide',),
        }),
        ('Javob Berish (Mas\'ul shaxs tomonidan)', {
            'fields': ('response_content', 'responded_by_display', 'responded_at'),
            'classes': ('wide',),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if 'response_content' in form.changed_data :
            current_response_content = form.cleaned_data.get('response_content')
            if current_response_content and (not obj.responded_by or obj.response_content != current_response_content):
                obj.responded_by = request.user
                obj.responded_at = timezone.now()
            elif not current_response_content: # Agar javob o'zgartirilsa
                obj.responded_by = None
                obj.responded_at = None

            if current_response_content and obj.status not in ['answered', 'closed']:
                 obj.status = 'answered'
            elif not current_response_content and obj.status == 'answered': # Agar javob o'chirilsa va status 'answered' bo'lsa
                 obj.status = 'seen' # Yoki 'new' ga qaytarish logikaga qarab
        super().save_model(request, obj, form, change)

    @admin.display(description='Mavzu (qisqa)')
    def subject_short(self, obj):
        return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject

    @admin.display(description='Talaba')
    def student_link(self, obj):
        if obj.student:
            url = reverse("admin:auth_app_student_change", args=[obj.student.pk])
            return format_html('<a href="{}">{}</a>', url, obj.student.short_name_api or obj.student.username)
        return "Noma'lum talaba"

    @admin.display(description='Mas\'ul shaxs')
    def responsible_person_link(self, obj):
        if obj.responsible_person:
            url = reverse("admin:auth_app_responsibleperson_change", args=[obj.responsible_person.pk])
            return format_html('<a href="{}">{}</a>', url, str(obj.responsible_person))
        return "Noma'lum mas'ul"

    @admin.display(description='Yuborilgan vaqti')
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')

    @admin.display(description='Javob berilgan vaqti')
    def responded_at_formatted(self, obj):
        return obj.responded_at.strftime('%Y-%m-%d %H:%M') if obj.responded_at else '-'

    @admin.display(description='Javob bergan shaxs')
    def responded_by_display(self, obj):
        return obj.responded_by.username if obj.responded_by else '-'
    
    @admin.display(description='Biriktirmalar', boolean=True)
    def has_attachments(self, obj):
        return obj.attachments.exists()
    has_attachments.admin_order_field = 'attachments_count' # get_queryset da annotate qilish kerak

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(attachments_count=Count('attachments', distinct=True))
        return qs
    
    def has_add_permission(self, request): # Xabarlar talabalar tomonidan yuboriladi
        return False