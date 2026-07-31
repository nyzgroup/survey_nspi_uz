from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Barcha modellar uchun demo ma'lumotlar yaratadi"

    def handle(self, *args, **kwargs):
        from auth_app.models import (
            Student, Survey, SurveyFile, Question, Choice,
            SurveyResponse, Answer, ResponsiblePerson,
            MessageToResponsible, MessageReply,
        )

        self.stdout.write(self.style.WARNING("Demo ma'lumotlar yaratilmoqda..."))

        with transaction.atomic():

            # --- Superuser ---
            # Zaif default parol ishlatilmaydi (FIND-001).
            # DEMO_ADMIN_PASSWORD env berilsa — shu ishlatiladi; aks holda random.
            import os
            import secrets
            admin, created = User.objects.get_or_create(
                username='admin',
                defaults={'is_staff': True, 'is_superuser': True, 'email': 'admin@nspi.uz'}
            )
            if created:
                demo_password = os.environ.get('DEMO_ADMIN_PASSWORD') or secrets.token_urlsafe(16)
                admin.set_password(demo_password)
                admin.save()
                self.stdout.write(self.style.SUCCESS(
                    f"  [+] Superuser: admin (parol bir marta ko'rsatiladi)"
                ))
                self.stdout.write(self.style.WARNING(
                    f"  [!] Admin parol: {demo_password}  — darhol saqlang va o'zgartiring!"
                ))
            else:
                self.stdout.write("  [~] Superuser 'admin' allaqachon mavjud (parol o'zgartirilmadi)")

            # --- Talabalar ---
            students_data = [
                {
                    'username': 'student001',
                    'student_id_number': '20240001',
                    'first_name': 'Jasur',
                    'last_name': 'Toshmatov',
                    'patronymic': 'Akbarovich',
                    'full_name_api': 'Toshmatov Jasur Akbarovich',
                    'short_name_api': 'Toshmatov J.',
                    'gender_code': '1', 'gender_name': 'Erkak',
                    'faculty_name_api': 'Informatika va raqamli texnologiyalar',
                    'faculty_code_api': 'IRT', 'faculty_id_api': 1,
                    'specialty_name_api': "Informatika va axborot texnologiyalari",
                    'specialty_code_api': '5330200',
                    'group_name_api': 'IRT-22-01', 'group_id_api': 101,
                    'level_code': '2', 'level_name': '2-kurs',
                    'education_form_name': 'Kunduzgi', 'education_form_code': '11',
                    'education_type_name': 'Bakalavr', 'education_type_code': '11',
                    'payment_form_name': "Davlat granti", 'payment_form_code': '1',
                    'student_status_name': 'Tahsil olmoqda', 'student_status_code': '1',
                    'semester_name_api': '4-semestr', 'semester_code_api': '4',
                    'university_name_api': 'NSPI',
                    'avg_gpa': '3.85',
                    'country_name_api': "O'zbekiston", 'country_code_api': 'UZ',
                    'province_name_api': 'Namangan viloyati', 'province_code_api': '08',
                    'district_name_api': 'Namangan tumani', 'district_code_api': '0801',
                },
                {
                    'username': 'student002',
                    'student_id_number': '20240002',
                    'first_name': 'Nilufar',
                    'last_name': 'Rahimova',
                    'patronymic': 'Saidovna',
                    'full_name_api': 'Rahimova Nilufar Saidovna',
                    'short_name_api': 'Rahimova N.',
                    'gender_code': '2', 'gender_name': 'Ayol',
                    'faculty_name_api': 'Matematika va tabiiy fanlar',
                    'faculty_code_api': 'MTF', 'faculty_id_api': 2,
                    'specialty_name_api': "Matematika va informatika",
                    'specialty_code_api': '5140200',
                    'group_name_api': 'MTF-23-02', 'group_id_api': 102,
                    'level_code': '1', 'level_name': '1-kurs',
                    'education_form_name': 'Kunduzgi', 'education_form_code': '11',
                    'education_type_name': 'Bakalavr', 'education_type_code': '11',
                    'payment_form_name': "To'lov-shartnoma", 'payment_form_code': '2',
                    'student_status_name': 'Tahsil olmoqda', 'student_status_code': '1',
                    'semester_name_api': '2-semestr', 'semester_code_api': '2',
                    'university_name_api': 'NSPI',
                    'avg_gpa': '4.20',
                    'country_name_api': "O'zbekiston", 'country_code_api': 'UZ',
                    'province_name_api': 'Namangan viloyati', 'province_code_api': '08',
                    'district_name_api': 'Pop tumani', 'district_code_api': '0804',
                },
                {
                    'username': 'student003',
                    'student_id_number': '20240003',
                    'first_name': 'Bobur',
                    'last_name': 'Yusupov',
                    'patronymic': 'Hamidovich',
                    'full_name_api': 'Yusupov Bobur Hamidovich',
                    'short_name_api': 'Yusupov B.',
                    'gender_code': '1', 'gender_name': 'Erkak',
                    'faculty_name_api': 'Pedagogika va psixologiya',
                    'faculty_code_api': 'PP', 'faculty_id_api': 3,
                    'specialty_name_api': "Boshlang'ich ta'lim",
                    'specialty_code_api': '5111100',
                    'group_name_api': 'PP-21-03', 'group_id_api': 103,
                    'level_code': '3', 'level_name': '3-kurs',
                    'education_form_name': 'Sirtqi', 'education_form_code': '12',
                    'education_type_name': 'Bakalavr', 'education_type_code': '11',
                    'payment_form_name': "Davlat granti", 'payment_form_code': '1',
                    'student_status_name': 'Tahsil olmoqda', 'student_status_code': '1',
                    'semester_name_api': '6-semestr', 'semester_code_api': '6',
                    'university_name_api': 'NSPI',
                    'avg_gpa': '3.50',
                    'country_name_api': "O'zbekiston", 'country_code_api': 'UZ',
                    'province_name_api': 'Namangan viloyati', 'province_code_api': '08',
                    'district_name_api': 'Uychi tumani', 'district_code_api': '0806',
                },
                {
                    'username': 'student004',
                    'student_id_number': '20240004',
                    'first_name': 'Maftuna',
                    'last_name': "Xo'jayeva",
                    'patronymic': 'Baxtiyorovna',
                    'full_name_api': "Xo'jayeva Maftuna Baxtiyorovna",
                    'short_name_api': "Xo'jayeva M.",
                    'gender_code': '2', 'gender_name': 'Ayol',
                    'faculty_name_api': 'Informatika va raqamli texnologiyalar',
                    'faculty_code_api': 'IRT', 'faculty_id_api': 1,
                    'specialty_name_api': "Kompyuter injiniringi",
                    'specialty_code_api': '5330100',
                    'group_name_api': 'IRT-22-02', 'group_id_api': 104,
                    'level_code': '2', 'level_name': '2-kurs',
                    'education_form_name': 'Kunduzgi', 'education_form_code': '11',
                    'education_type_name': 'Bakalavr', 'education_type_code': '11',
                    'payment_form_name': "To'lov-shartnoma", 'payment_form_code': '2',
                    'student_status_name': 'Tahsil olmoqda', 'student_status_code': '1',
                    'semester_name_api': '4-semestr', 'semester_code_api': '4',
                    'university_name_api': 'NSPI',
                    'avg_gpa': '4.50',
                    'country_name_api': "O'zbekiston", 'country_code_api': 'UZ',
                    'province_name_api': 'Namangan viloyati', 'province_code_api': '08',
                    'district_name_api': 'Chortoq tumani', 'district_code_api': '0803',
                },
                {
                    'username': 'student005',
                    'student_id_number': '20240005',
                    'first_name': 'Sherzod',
                    'last_name': 'Mirzayev',
                    'patronymic': 'Olimovich',
                    'full_name_api': 'Mirzayev Sherzod Olimovich',
                    'short_name_api': 'Mirzayev Sh.',
                    'gender_code': '1', 'gender_name': 'Erkak',
                    'faculty_name_api': 'Matematika va tabiiy fanlar',
                    'faculty_code_api': 'MTF', 'faculty_id_api': 2,
                    'specialty_name_api': "Fizika va astronomiya",
                    'specialty_code_api': '5140500',
                    'group_name_api': 'MTF-22-01', 'group_id_api': 105,
                    'level_code': '2', 'level_name': '2-kurs',
                    'education_form_name': 'Kunduzgi', 'education_form_code': '11',
                    'education_type_name': 'Bakalavr', 'education_type_code': '11',
                    'payment_form_name': "Davlat granti", 'payment_form_code': '1',
                    'student_status_name': 'Tahsil olmoqda', 'student_status_code': '1',
                    'semester_name_api': '4-semestr', 'semester_code_api': '4',
                    'university_name_api': 'NSPI',
                    'avg_gpa': '3.70',
                    'country_name_api': "O'zbekiston", 'country_code_api': 'UZ',
                    'province_name_api': 'Namangan viloyati', 'province_code_api': '08',
                    'district_name_api': 'Kosonsoy tumani', 'district_code_api': '0805',
                },
            ]

            students = []
            for data in students_data:
                st, created = Student.objects.get_or_create(
                    username=data['username'],
                    defaults={**data, 'last_login_api': timezone.now()}
                )
                students.append(st)
                status = "[+]" if created else "[~]"
                self.stdout.write(f"  {status} Talaba: {st.full_name_api}")

            # --- Mas'ul shaxslar ---
            responsible_data = [
                {
                    'first_name': 'Akbar', 'last_name': 'Nazarov', 'patronymic': 'Hamidovich',
                    'position': 'Dekan muovini (o\'quv ishlari bo\'yicha)',
                    'phone_number': '+998901234567',
                    'telegram_username': '@nazarov_akbar',
                    'email': 'nazarov@nspi.uz',
                    'office_location': '2-bino, 201-xona',
                    'responsibilities_short': "O'quv jarayoni, dars jadvali, imtihonlar bo'yicha murojaat qiling.",
                    'is_active': True,
                },
                {
                    'first_name': 'Dilnoza', 'last_name': 'Karimova', 'patronymic': 'Rustamovna',
                    'position': 'Psixolog (tyutor)',
                    'phone_number': '+998901234568',
                    'telegram_username': '@karimova_psixolog',
                    'email': 'karimova@nspi.uz',
                    'office_location': '1-bino, 105-xona',
                    'responsibilities_short': "Psixologik yordam, stress va muammolarni hal qilish bo'yicha murojaat qiling.",
                    'is_active': True,
                },
                {
                    'first_name': 'Sardor', 'last_name': 'Tursunov', 'patronymic': 'Bekovich',
                    'position': 'Talabalar ishlari bo\'yicha prorektor',
                    'phone_number': '+998901234569',
                    'telegram_username': '@tursunov_prorektor',
                    'email': 'tursunov@nspi.uz',
                    'office_location': 'Bosh bino, 301-xona',
                    'responsibilities_short': "Talabalar turmush sharoiti, yotoqxona, ijtimoiy masalalar bo'yicha murojaat qiling.",
                    'is_active': True,
                },
            ]

            responsibles = []
            for data in responsible_data:
                rp, created = ResponsiblePerson.objects.get_or_create(
                    email=data['email'], defaults=data
                )
                responsibles.append(rp)
                status = "[+]" if created else "[~]"
                self.stdout.write(f"  {status} Mas'ul shaxs: {rp.full_name} — {rp.position}")

            # --- So'rovnomalar ---
            survey1, created = Survey.objects.get_or_create(
                title="O'quv jarayoni sifatini baholash (2024-2025)",
                defaults={
                    'purpose': "Talabalarning o'quv jarayonidan qoniqish darajasini aniqlash va ta'lim sifatini yaxshilash.",
                    'description': "Ushbu so'rovnoma natijalari o'quv jarayonini takomillashtirish uchun ishlatiladi. Iltimos, to'g'ri va halol javob bering.",
                    'start_date': timezone.now() - timezone.timedelta(days=10),
                    'end_date': timezone.now() + timezone.timedelta(days=20),
                    'is_active': True,
                    'is_anonymous': False,
                    'created_by': admin,
                }
            )
            self.stdout.write(f"  {'[+]' if created else '[~]'} So'rovnoma: {survey1.title}")

            survey2, created = Survey.objects.get_or_create(
                title="Yotoqxona sharoitlari haqida fikr-mulohaza",
                defaults={
                    'purpose': "Yotoqxona xizmatlarini yaxshilash maqsadida talabalar fikrlarini yig'ish.",
                    'description': "Anonim so'rovnoma. Javoblaringiz maxfiy saqlanadi.",
                    'start_date': timezone.now() - timezone.timedelta(days=5),
                    'end_date': timezone.now() + timezone.timedelta(days=25),
                    'is_active': True,
                    'is_anonymous': True,
                    'created_by': admin,
                }
            )
            self.stdout.write(f"  {'[+]' if created else '[~]'} So'rovnoma: {survey2.title}")

            survey3, created = Survey.objects.get_or_create(
                title="Sport va madaniy tadbirlar bo'yicha so'rovnoma",
                defaults={
                    'purpose': "Talabalarning sport va madaniy tadbirlarga bo'lgan qiziqishini aniqlash.",
                    'description': "Universitetda qanday sport va madaniy tadbirlar o'tkazilishini istaysiz?",
                    'start_date': timezone.now() + timezone.timedelta(days=5),
                    'end_date': timezone.now() + timezone.timedelta(days=35),
                    'is_active': True,
                    'is_anonymous': False,
                    'created_by': admin,
                }
            )
            self.stdout.write(f"  {'[+]' if created else '[~]'} So'rovnoma (kelgusi): {survey3.title}")

            # --- Savollar va variantlar (Survey 1) ---
            if not survey1.questions.exists():
                q1 = Question.objects.create(
                    survey=survey1, order=1,
                    text="O'qituvchilarning dars berish sifatini qanday baholaysiz?",
                    question_type='single_choice', is_required=True
                )
                for txt in ["A'lo (5)", "Yaxshi (4)", "Qoniqarli (3)", "Qoniqarsiz (2)"]:
                    Choice.objects.create(question=q1, text=txt)

                q2 = Question.objects.create(
                    survey=survey1, order=2,
                    text="Qaysi fanlar bo'yicha qo'shimcha darslar kerak deb hisoblaysiz?",
                    question_type='multiple_choice', is_required=False
                )
                for txt in ['Matematika', 'Informatika', "Ingliz tili", "Fizika", "Kimyo", "Tarix"]:
                    Choice.objects.create(question=q2, text=txt)

                q3 = Question.objects.create(
                    survey=survey1, order=3,
                    text="Kutubxona xizmatidan qoniqasizmi?",
                    question_type='single_choice', is_required=True
                )
                for txt in ["Ha, to'liq qoniqaman", "Qisman qoniqaman", "Qoniqmayman"]:
                    Choice.objects.create(question=q3, text=txt)

                q4 = Question.objects.create(
                    survey=survey1, order=4,
                    text="O'quv jarayonini yaxshilash bo'yicha takliflaringiz:",
                    question_type='text', is_required=False
                )
                self.stdout.write(f"  [+] {survey1.title} uchun 4 ta savol yaratildi")

            # --- Savollar (Survey 2) ---
            if not survey2.questions.exists():
                q5 = Question.objects.create(
                    survey=survey2, order=1,
                    text="Yotoqxona xonalarining tozaligi qanday darajada?",
                    question_type='single_choice', is_required=True
                )
                for txt in ["Juda yaxshi", "Yaxshi", "O'rtacha", "Yomon"]:
                    Choice.objects.create(question=q5, text=txt)

                q6 = Question.objects.create(
                    survey=survey2, order=2,
                    text="Yotoqxonada qaysi muammolar mavjud?",
                    question_type='multiple_choice', is_required=False
                )
                for txt in ["Internet tezligi past", "Issiq suv yo'q", "Tozalik yetarli emas",
                            "Shovqin ko'p", "Oziq-ovqat sifati past", "Boshqa"]:
                    Choice.objects.create(question=q6, text=txt)

                q7 = Question.objects.create(
                    survey=survey2, order=3,
                    text="Yotoqxona xizmati haqida qo'shimcha fikrlaringiz:",
                    question_type='text', is_required=False
                )
                self.stdout.write(f"  [+] {survey2.title} uchun 3 ta savol yaratildi")

            # --- Savollar (Survey 3) ---
            if not survey3.questions.exists():
                q8 = Question.objects.create(
                    survey=survey3, order=1,
                    text="Qaysi sport turlarida qatnashishni xohlaysiz?",
                    question_type='multiple_choice', is_required=True
                )
                for txt in ["Futbol", "Voleybol", "Basketbol", "Tennis", "Suzish", "Kurash", "Karate"]:
                    Choice.objects.create(question=q8, text=txt)

                q9 = Question.objects.create(
                    survey=survey3, order=2,
                    text="Madaniy tadbirlardan qaysi birlarini afzal ko'rasiz?",
                    question_type='multiple_choice', is_required=True
                )
                for txt in ["KVN", "Konsert", "Film ko'rsatuvi", "Sayohat", "Ko'rgazma", "Musobaqa"]:
                    Choice.objects.create(question=q9, text=txt)
                self.stdout.write(f"  [+] {survey3.title} uchun 2 ta savol yaratildi")

            # --- Javoblar (faqat Survey 1 uchun) ---
            q1 = survey1.questions.get(order=1)
            q2 = survey1.questions.get(order=2)
            q3 = survey1.questions.get(order=3)
            q4 = survey1.questions.get(order=4)

            text_answers = [
                "Darslar qiziqarli, lekin laboratoriya qurilmalari yangilanishi kerak.",
                "Internet tezligini oshirish kerak, kutubxona vaqtini uzaytirish ham yaxshi bo'lardi.",
                "Amaliy mashg'ulotlar ko'proq bo'lishi kerak.",
                "Umuman olganda yaxshi, faqat ba'zi o'qituvchilar dars jadvalini buzishadi.",
            ]

            for i, student in enumerate(students[:4]):
                if not SurveyResponse.objects.filter(survey=survey1, student=student).exists():
                    resp = SurveyResponse.objects.create(survey=survey1, student=student)

                    # Q1 - single choice
                    choices_q1 = list(q1.choices.all())
                    ans1 = Answer.objects.create(
                        survey_response=resp, question=q1,
                        selected_choice=choices_q1[i % len(choices_q1)]
                    )

                    # Q2 - multiple choice
                    choices_q2 = list(q2.choices.all())
                    ans2 = Answer.objects.create(survey_response=resp, question=q2)
                    selected = random.sample(choices_q2, random.randint(1, 3))
                    ans2.selected_choices.set(selected)

                    # Q3 - single choice
                    choices_q3 = list(q3.choices.all())
                    Answer.objects.create(
                        survey_response=resp, question=q3,
                        selected_choice=choices_q3[i % len(choices_q3)]
                    )

                    # Q4 - text
                    Answer.objects.create(
                        survey_response=resp, question=q4,
                        text_answer=text_answers[i]
                    )

                    self.stdout.write(f"  [+] Javob: {student.short_name_api} → {survey1.title[:40]}")

            # --- Xabarlar ---
            msg_subjects = [
                ("Dars jadvalida o'zgarish haqida", "Assalomu alaykum! Bugun 3-juft dars bekor qilinganini eshitdim, lekin rasmiy ma'lumot yo'q. Iltimos, aniqlab bering."),
                ("Imtihon topshiriq muddati haqida", "Salom! Kurs ishi topshirish muddati uzaytirilishi mumkinmi? Bir nechta talaba kasal bo'lib qoldi."),
                ("Stipendiya to'lovi haqida", "Assalomu alaykum, bu oygi stipendiya kechikmoqda. Sababi nima ekanini bilsam bo'ladimi?"),
            ]

            for i, (subject, content) in enumerate(msg_subjects):
                student = students[i]
                responsible = responsibles[i % len(responsibles)]
                if not MessageToResponsible.objects.filter(student=student, subject=subject).exists():
                    msg = MessageToResponsible.objects.create(
                        student=student,
                        responsible_person=responsible,
                        subject=subject,
                        content=content,
                        status='new' if i == 0 else ('seen' if i == 1 else 'answered'),
                    )
                    self.stdout.write(f"  [+] Xabar: {student.short_name_api} → {responsible.last_name}: '{subject[:40]}'")

                    if msg.status == 'answered':
                        MessageReply.objects.get_or_create(
                            message=msg,
                            defaults={
                                'content': "Assalomu alaykum! Stipendiya to'lovi 3 ish kuni ichida amalga oshiriladi. Sababi bank tizimidagi texnik nosozlik edi.",
                                'replied_by': admin,
                            }
                        )
                        self.stdout.write(f"    [+] Javob qo'shildi")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write(self.style.SUCCESS("  Demo ma'lumotlar muvaffaqiyatli yaratildi!"))
        self.stdout.write(self.style.SUCCESS("=" * 55))
        self.stdout.write(f"  Admin panel:  http://localhost:8000/admin/")
        self.stdout.write(f"  Login:        admin / admin123")
        self.stdout.write(f"  Talabalar:    {Student.objects.count()} ta")
        self.stdout.write(f"  So'rovnomalar:{Survey.objects.count()} ta")
        self.stdout.write(f"  Mas'ul shaxslar: {ResponsiblePerson.objects.count()} ta")
        self.stdout.write(f"  Javoblar:     {SurveyResponse.objects.count()} ta")
        self.stdout.write(f"  Xabarlar:     {MessageToResponsible.objects.count()} ta")
        self.stdout.write(self.style.SUCCESS("=" * 55))
