# auth_app/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings # Foydalanuvchi modelini olish uchun (agar Student o'rniga standart User ishlatilsa)
import os # Fayl nomini tozalash uchun
from uuid import uuid4 # Unikal fayl nomlari uchun

# --- Mavjud Student modeli (o'zgarishsiz qoldiriladi) ---
class Student(models.Model):
    username = models.CharField(
        max_length=150, unique=True,
        verbose_name="Foydalanuvchi nomi (login)",
        help_text="Tizimga kirish uchun foydalaniladigan login (Talaba ID raqami)"
    )
    student_id_number = models.CharField(max_length=50, unique=True, null=True, blank=True,
                                         verbose_name="Talaba ID raqami (API)",
                                         help_text="API dan olingan talabaning ID raqami")
    api_user_hash = models.CharField(max_length=255, unique=True, null=True, blank=True,
                                     verbose_name="API foydalanuvchi hash",
                                     help_text="API dagi foydalanuvchi uchun unikal SHA256 hash")
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ismi")
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Familiyasi") # API dagi 'second_name'
    patronymic = models.CharField(max_length=100, blank=True, null=True, verbose_name="Otasining ismi") # API dagi 'third_name'
    full_name_api = models.CharField(max_length=255, blank=True, null=True, verbose_name="To'liq F.I.Sh. (API)")
    short_name_api = models.CharField(max_length=100, blank=True, null=True, verbose_name="Qisqa F.I.Sh. (API)")

    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Talabning surati (URL)")
    birth_date_timestamp = models.BigIntegerField(null=True, blank=True, verbose_name="Tug'ilgan sana (timestamp)")
    passport_pin = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pasport PIN")
    passport_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Pasport raqami")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=30, blank=True, null=True, verbose_name="Telefon raqami")

    gender_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Jinsi kodi")
    gender_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Jinsi")

    university_name_api = models.CharField(max_length=255, blank=True, null=True, verbose_name="Universitet nomi (API)")

    # Specialty (Mutaxassislik)
    specialty_id_api = models.CharField(max_length=100, blank=True, null=True, verbose_name="Mutaxassislik ID (API)")
    specialty_code_api = models.CharField(max_length=50, blank=True, null=True, verbose_name="Mutaxassislik kodi (API)")
    specialty_name_api = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mutaxassislik nomi (API)")

    # Student Status
    student_status_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Talaba status kodi")
    student_status_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Talaba statusi")

    # Education Form (Ta'lim shakli)
    education_form_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ta'lim shakli kodi")
    education_form_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ta'lim shakli")

    # Education Type (Ta'lim turi)
    education_type_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ta'lim turi kodi")
    education_type_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ta'lim turi")

    # Payment Form (To'lov shakli)
    payment_form_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="To'lov shakli kodi")
    payment_form_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="To'lov shakli")

    # Group
    group_id_api = models.IntegerField(null=True, blank=True, verbose_name="Guruh ID (API)")
    group_name_api = models.CharField(max_length=100, blank=True, null=True, verbose_name="Guruh nomi (API)")
    group_education_lang_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Guruh ta'lim tili kodi")
    group_education_lang_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Guruh ta'lim tili")

    # Faculty
    faculty_id_api = models.IntegerField(null=True, blank=True, verbose_name="Fakultet ID (API)")
    faculty_name_api = models.CharField(max_length=255, blank=True, null=True, verbose_name="Fakultet nomi (API)")
    faculty_code_api = models.CharField(max_length=50, blank=True, null=True, verbose_name="Fakultet kodi (API)")

    # Education Language (Asosiy ta'lim tili, guruhnikidan farqli bo'lishi mumkin)
    education_lang_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ta'lim tili kodi")
    education_lang_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ta'lim tili")

    # Level (Kurs)
    level_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Kurs kodi") # API dagi 'level.code'
    level_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Kurs nomi") # API dagi 'level.name' (kurs nomi)

    # Semester
    semester_id_api = models.IntegerField(null=True, blank=True, verbose_name="Semestr ID (API)")
    semester_code_api = models.CharField(max_length=10, blank=True, null=True, verbose_name="Semestr kodi (API)")
    semester_name_api = models.CharField(max_length=100, blank=True, null=True, verbose_name="Semestr nomi (API)")
    semester_is_current = models.BooleanField(null=True, blank=True, verbose_name="Joriy semestr")
    semester_education_year_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Semestr o'quv yili kodi")
    semester_education_year_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Semestr o'quv yili nomi")
    semester_education_year_is_current = models.BooleanField(null=True, blank=True, verbose_name="Joriy o'quv yili (semestr)")

    avg_gpa = models.CharField(max_length=10, blank=True, null=True, verbose_name="O'rtacha ball (GPA)") # String sifatida, chunki '3.50'
    password_is_valid_api = models.BooleanField(null=True, blank=True, verbose_name="Parol to'g'riligi (API)")

    address_api = models.TextField(blank=True, null=True, verbose_name="Manzil (API)")

    # Country
    country_code_api = models.CharField(max_length=10, blank=True, null=True, verbose_name="Davlat kodi (API)")
    country_name_api = models.CharField(max_length=100, blank=True, null=True, verbose_name="Davlat nomi (API)")

    # Province (Viloyat)
    province_code_api = models.CharField(max_length=20, blank=True, null=True, verbose_name="Viloyat kodi (API)")
    province_name_api = models.CharField(max_length=100, blank=True, null=True, verbose_name="Viloyat nomi (API)")

    # District (Tuman)
    district_code_api = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tuman kodi (API)")
    district_name_api = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tuman nomi (API)")

    # Social Category
    social_category_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Ijtimoiy toifa kodi")
    social_category_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ijtimoiy toifa nomi")

    # Accommodation (Turar joyi)
    accommodation_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="Turar joy kodi")
    accommodation_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Turar joy nomi")

    validate_url_api = models.URLField(max_length=500, blank=True, null=True, verbose_name="Validatsiya havolasi (API)")

    # Tizim uchun ma'lumotlar
    last_login_api = models.DateTimeField(null=True, blank=True, verbose_name="Oxirgi kirish (API)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqti")

    def __str__(self):
        return self.full_name_api or f"{self.last_name or ''} {self.first_name or ''}".strip() or self.username

    class Meta:
        verbose_name = "Talaba (API)"
        verbose_name_plural = "Talabalar (API)"
        ordering = ['-updated_at', 'last_name', 'first_name']

    @property
    def get_birth_date_display(self):
        if self.birth_date_timestamp:
            try:
                dt_object = timezone.datetime.fromtimestamp(self.birth_date_timestamp, tz=timezone.get_current_timezone())
                return dt_object.strftime('%d-%m-%Y')
            except (ValueError, TypeError, OSError): # Potensial xatoliklarni ushlash
                return "Noma'lum sana (xato)"
        return None

# --- So'rovnoma uchun yangi modellar ---

def survey_file_upload_path(instance, filename):
    """
    So'rovnoma fayllari uchun unikal yuklash yo'lini generatsiya qiladi.
    Masalan: surveys/<survey_pk>/<uuid>.<extension>
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid4()}.{ext}"
    return os.path.join('surveys', str(instance.survey.pk), filename)

class Survey(models.Model):
    title = models.CharField(max_length=255, verbose_name="So'rovnoma nomi")
    purpose = models.TextField(verbose_name="So'rovnoma maqsadi", blank=True, null=True)
    description = models.TextField(verbose_name="Mazmuni / Tavsifi", blank=True, null=True)
    
    start_date = models.DateTimeField(verbose_name="Boshlanish sanasi", default=timezone.now)
    end_date = models.DateTimeField(verbose_name="Tugash sanasi", null=True, blank=True,
                                    help_text="Agar bo'sh qoldirilsa, so'rovnoma muddatsiz bo'ladi.")
    
    is_active = models.BooleanField(default=True, verbose_name="Aktivmi?",
                                     help_text="Aktiv bo'lmagan so'rovnomalar talabalarga ko'rinmaydi.")
    is_anonymous = models.BooleanField(default=False, verbose_name="Anonimmi?",
                                        help_text="Agar anonim bo'lsa, talaba shaxsi javoblarga bog'lanmaydi.")
    
    # Agar so'rovnoma ma'lum bir guruh yoki fakultet uchun bo'lsa, bu yerga ForeignKey qo'shish mumkin.
    # Masalan: target_faculty = models.ForeignKey('Faculty', null=True, blank=True, on_delete=models.SET_NULL)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Agar Django standart User modeli adminlar uchun ishlatilsa
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_surveys',
        verbose_name="Yaratuvchi (Admin)"
    ) # Agar Student modeli admin sifatida ishlatilsa, Student ga bog'lash mumkin.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "So'rovnoma"
        verbose_name_plural = "So'rovnomalar"
        ordering = ['-created_at']

    @property
    def is_open(self):
        """So'rovnoma hozirda ochiq yoki yo'qligini tekshiradi."""
        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_date > now:
            return False # Hali boshlanmagan
        if self.end_date and self.end_date < now:
            return False # Muddati tugagan
        return True
    
    @property
    def total_responses(self):
        """Ushbu so'rovnomaga berilgan umumiy javoblar soni."""
        return self.responses.count() # surveyresponse_set.count() bilan bir xil

class SurveyFile(models.Model):
    survey = models.ForeignKey(Survey, related_name='files', on_delete=models.CASCADE, verbose_name="So'rovnoma")
    file = models.FileField(upload_to=survey_file_upload_path, verbose_name="Fayl/Rasm")
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name="Izoh (ixtiyoriy)")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.survey.title} - {os.path.basename(self.file.name)}"

    class Meta:
        verbose_name = "So'rovnoma fayli"
        verbose_name_plural = "So'rovnoma fayllari"

class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'Matnli javob'),
        ('single_choice', 'Yagona tanlov'),
        ('multiple_choice', 'Ko\'p tanlov'),
        # ('rating', 'Reyting (yulduzchalar)'), # Kelajakda qo'shish mumkin
        # ('yes_no', 'Ha / Yo\'q'),
    ]
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE, verbose_name="So'rovnoma")
    text = models.TextField(verbose_name="Savol matni")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='text',
        verbose_name="Savol turi"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami",
                                        help_text="Savollarni ko'rsatish tartibi.")
    is_required = models.BooleanField(default=True, verbose_name="Majburiymi?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.survey.title[:30]}... - Savol: {self.text[:50]}..."

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['survey', 'order', 'created_at'] # Avval so'rovnoma bo'yicha, keyin tartib raqami bo'yicha

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE, verbose_name="Savol")
    text = models.CharField(max_length=255, verbose_name="Variant matni")
    # `order` maydoni qo'shish mumkin, agar variantlar tartibi muhim bo'lsa
    # order = models.PositiveIntegerField(default=0, verbose_name="Tartib raqami")

    def __str__(self):
        return f"{self.question.text[:30]}... - Variant: {self.text}"

    class Meta:
        verbose_name = "Tanlov varianti"
        verbose_name_plural = "Tanlov variantlari"
        # ordering = ['question', 'order'] # Agar 'order' qo'shilsa

class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, related_name='responses', on_delete=models.CASCADE, verbose_name="So'rovnoma")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='survey_responses', verbose_name="Talaba")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqti")

    class Meta:
        verbose_name = "So'rovnoma javobi (Ishtirok)"
        verbose_name_plural = "So'rovnoma javoblari (Ishtiroklar)"
        unique_together = ('survey', 'student')  # Only if not anonymous
        ordering = ['-submitted_at']

    def __str__(self):
        student_name = "Anonim" if not self.student else str(self.student)
        return f"{self.survey.title} - {student_name} ({self.submitted_at.strftime('%Y-%m-%d %H:%M')})"

class Answer(models.Model):
    """Talabaning har bir savolga bergan javobi."""
    survey_response = models.ForeignKey(SurveyResponse, related_name='answers', on_delete=models.CASCADE, verbose_name="So'rovnoma ishtiroki")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_answer = models.TextField(null=True, blank=True)
    selected_choice = models.ForeignKey(
        Choice, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='chosen_in_answers', verbose_name="Tanlangan yagona variant"
    )
    # Agar 'multiple_choice' bo'lsa, ManyToManyField (Choice)
    selected_choices = models.ManyToManyField(
        Choice, blank=True, 
        related_name='multi_chosen_in_answers', verbose_name="Tanlangan ko'p variantlar"
    )

    answered_at = models.DateTimeField(auto_now_add=True) # Bu aslida SurveyResponse.submitted_at bilan bir xil bo'ladi

    class Meta:
        verbose_name = "Javob"
        verbose_name_plural = "Javoblar"
        # Bir ishtirokda bir savolga faqat bitta javob bo'lishi kerak (agar savol turi buni talab qilsa)
        unique_together = ('survey_response', 'question')
        ordering = ['survey_response', 'question__order']

    def __str__(self):
        if self.question.question_type == 'text':
            return f"Javob (ID: {self.pk}): {self.text_answer[:50]}..."
        elif self.question.question_type == 'single_choice' and self.selected_choice:
            return f"Javob (ID: {self.pk}): {self.selected_choice.text}"
        elif self.question.question_type == 'multiple_choice':
            choices_text = ", ".join([choice.text for choice in self.selected_choices.all()])
            return f"Javob (ID: {self.pk}): [{choices_text}]"
        return f"Javob (ID: {self.pk}) - Savol: {self.question.text[:30]}..."

    def clean(self):
        """
        Javob turini savol turiga mosligini tekshiradi.
        Masalan, matnli savolga `selected_choice` berilmasligi kerak.
        """
        from django.core.exceptions import ValidationError
        q_type = self.question.question_type

        if q_type == 'text':
            if self.selected_choice or self.selected_choices.exists():
                raise ValidationError("Matnli savol uchun tanlov varianti berilmasligi kerak.")
            if not self.text_answer: # Agar matnli javob majburiy bo'lsa
                # Bu logikani `is_required` ga bog'liq qilish kerak
                # pass # Hozircha, bo'sh matnli javobga ruxsat beramiz (agar Question.is_required=False bo'lsa)
                pass
        elif q_type == 'single_choice':
            if self.text_answer or self.selected_choices.exists():
                raise ValidationError("Yagona tanlovli savol uchun matnli javob yoki ko'p tanlov berilmasligi kerak.")
            if self.question.is_required and not self.selected_choice:
                 raise ValidationError("Yagona tanlovli majburiy savol uchun variant tanlanmagan.")
        elif q_type == 'multiple_choice':
            if self.text_answer or self.selected_choice:
                raise ValidationError("Ko'p tanlovli savol uchun matnli javob yoki yagona tanlov berilmasligi kerak.")
            if self.question.is_required and not self.selected_choices.exists():
                 raise ValidationError("Ko'p tanlovli majburiy savol uchun kamida bitta variant tanlanmagan.")
        # Boshqa savol turlari uchun ham tekshiruvlar qo'shish mumkin

    def save(self, *args, **kwargs):
        # `clean` metodini avtomatik chaqirish (ixtiyoriy, lekin yaxshi amaliyot)
        # self.full_clean() # Agar model formadan tashqari yaratilsa, bu foydali
        super().save(*args, **kwargs)

class ResponsiblePerson(models.Model):
    """Adminlar tomonidan yaratiladigan, talabalar murojaat qilishi mumkin bo'lgan mas'ul shaxslar."""
    first_name = models.CharField(max_length=100, verbose_name="Ismi")
    last_name = models.CharField(max_length=100, verbose_name="Familiyasi")
    patronymic = models.CharField(max_length=100, blank=True, null=True, verbose_name="Otasining ismi (ixtiyoriy)")
    position = models.CharField(max_length=255, verbose_name="Lavozimi",
                                help_text="Masalan, Dekan muovini, Tyutor, Kafedra mudiri")
    
    # Qo'shimcha aloqa ma'lumotlari (ixtiyoriy)
    email = models.EmailField(blank=True, null=True, verbose_name="Elektron pochta")
    phone_number = models.CharField(max_length=30, blank=True, null=True, verbose_name="Telefon raqami")
    office_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Xonasi / Joylashuvi")
    
    # Mas'ul shaxsga murojaat qilish mumkin bo'lgan sohalar yoki qisqa tavsif
    responsibilities_short = models.TextField(blank=True, null=True, verbose_name="Mas'uliyat sohalari (qisqacha)",
                                           help_text="Talabalar qanday masalalarda murojaat qilishi mumkinligi haqida.")

    is_active = models.BooleanField(default=True, verbose_name="Aktivmi?",
                                     help_text="Aktiv bo'lmagan shaxslar talabalarga ko'rinmaydi.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.position}"

    @property
    def full_name(self):
        name_parts = [self.last_name, self.first_name, self.patronymic]
        return " ".join(filter(None, name_parts))

    class Meta:
        verbose_name = "Mas'ul shaxs"
        verbose_name_plural = "Mas'ul shaxslar"
        ordering = ['last_name', 'first_name']


def message_attachment_upload_path(instance, filename):
    """
    Xabarga biriktirilgan fayllar uchun unikal yuklash yo'lini generatsiya qiladi.
    Masalan: messages_attachments/<student_id>/<message_id>/<uuid>.<extension>
    """
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid4()}.{ext}"
    student_identifier = str(instance.message.student.id) if instance.message.student else "unknown_student"
    message_identifier = str(instance.message.id) if instance.message.id else "new_message"
    
    # Fayl nomini xavfsizroq qilish (ixtiyoriy, lekin yaxshi amaliyot)
    # from django.utils.text import get_valid_filename
    # filename = get_valid_filename(unique_filename)

    return os.path.join('messages_attachments', student_identifier, message_identifier, unique_filename)


class MessageToResponsible(models.Model):
    """Talabaning mas'ul shaxsga yuborgan xabari."""
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('seen', 'Ko\'rildi'),
        ('answered', 'Javob berildi'),
        ('pending', 'Kutilmoqda'), # Masalan, qo'shimcha ma'lumot kutilayotgan bo'lsa
        ('closed', 'Yopilgan'),  # Muammo hal qilingan yoki boshqa sabab
    ]

    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, # Agar talaba o'chirilsa, uning xabarlari ham o'chiriladi
        related_name='sent_messages_to_responsible',
        verbose_name="Yuboruvchi talaba"
    )
    responsible_person = models.ForeignKey(
        ResponsiblePerson,
        on_delete=models.SET_NULL, # Agar mas'ul shaxs o'chirilsa, xabar qoladi, lekin kimga yuborilgani noma'lum bo'ladi
        null=True, # Yoki PROTECT, agar mas'ul shaxsni o'chirishdan oldin xabarlarni boshqasiga o'tkazish kerak bo'lsa
        related_name='received_messages_from_students',
        verbose_name="Qabul qiluvchi mas'ul shaxs"
    )
    subject = models.CharField(max_length=255, verbose_name="Xabar mavzusi")
    content = models.TextField(verbose_name="Xabar mazmuni")
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Xabar holati"
    )
    
    # Admin/Mas'ul shaxs tomonidan berilgan javob (agar tizim ichida javob berilsa)
    response_content = models.TextField(blank=True, null=True, verbose_name="Javob (mas'ul shaxsdan)")
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Javob bergan admin yoki mas'ul shaxs (agar ular ham User modeli bo'lsa)
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='responded_messages',
        verbose_name="Javob bergan shaxs"
    )
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name="Javob berilgan vaqti")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqti")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Oxirgi yangilanish") # Holat o'zgarganda

    # Talabaning xabarni ko'rganligini belgilash uchun (agar kerak bo'lsa)
    # is_read_by_student = models.BooleanField(default=False, verbose_name="Talaba tomonidan o'qildimi?")

    def __str__(self):
        return f"Xabar: {self.subject} (Talaba: {self.student.short_name_api or self.student.username} -> Mas'ul: {self.responsible_person})"

    class Meta:
        verbose_name = "Mas'ul shaxsga xabar"
        verbose_name_plural = "Mas'ul shaxslarga xabarlar"
        ordering = ['-created_at']

class MessageAttachment(models.Model):
    """Xabarga biriktirilgan fayllar (PDF, JPG, PNG, MP3, va hokazo)."""
    message = models.ForeignKey(
        MessageToResponsible, 
        related_name='attachments', 
        on_delete=models.CASCADE,
        verbose_name="Xabar"
    )
    file = models.FileField(
        upload_to=message_attachment_upload_path, 
        verbose_name="Biriktirilgan fayl",
        help_text="Ruxsat etilgan formatlar: PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG, MP3, WAV, OGG, MP4, MOV, AVI."
        # Fayl turlarini cheklash uchun validatsiya qo'shish kerak bo'ladi (masalan, forms.py da yoki model.clean() da)
    )
    original_filename = models.CharField(max_length=255, blank=True, verbose_name="Asl fayl nomi (avtomatik)")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Biriktirma: {self.original_filename or os.path.basename(self.file.name)} (Xabar ID: {self.message_id})"

    class Meta:
        verbose_name = "Xabarga biriktirma"
        verbose_name_plural = "Xabarga biriktirmalar"

    @property
    def file_type(self):
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()
    
    @property
    def file_size_kb(self):
        if self.file and hasattr(self.file, 'size'):
            return round(self.file.size / 1024, 2)
        return 0
