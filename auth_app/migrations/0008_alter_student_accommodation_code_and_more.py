# Generated by Django 4.2.20 on 2025-06-15 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0007_alter_answer_selected_choice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='accommodation_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Turar joy kodi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='accommodation_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Turar joy nomi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='address_api',
            field=models.TextField(blank=True, null=True, verbose_name='Manzil (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='api_user_hash',
            field=models.CharField(blank=True, help_text='API dagi foydalanuvchi uchun unikal SHA256 hash', max_length=255, null=True, unique=True, verbose_name='API foydalanuvchi hash'),
        ),
        migrations.AlterField(
            model_name='student',
            name='avg_gpa',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name="O'rtacha ball (GPA)"),
        ),
        migrations.AlterField(
            model_name='student',
            name='birth_date_timestamp',
            field=models.BigIntegerField(blank=True, null=True, verbose_name="Tug'ilgan sana (timestamp)"),
        ),
        migrations.AlterField(
            model_name='student',
            name='country_code_api',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Davlat kodi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='country_name_api',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Davlat nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqti'),
        ),
        migrations.AlterField(
            model_name='student',
            name='district_code_api',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Tuman kodi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='district_name_api',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Tuman nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='education_form_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name="Ta'lim shakli kodi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='education_form_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Ta'lim shakli"),
        ),
        migrations.AlterField(
            model_name='student',
            name='education_lang_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name="Ta'lim tili kodi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='education_lang_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="Ta'lim tili"),
        ),
        migrations.AlterField(
            model_name='student',
            name='education_type_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name="Ta'lim turi kodi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='education_type_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Ta'lim turi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='student',
            name='faculty_code_api',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Fakultet kodi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='faculty_id_api',
            field=models.IntegerField(blank=True, null=True, verbose_name='Fakultet ID (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='faculty_name_api',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Fakultet nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='first_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Ismi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='full_name_api',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="To'liq F.I.Sh. (API)"),
        ),
        migrations.AlterField(
            model_name='student',
            name='gender_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Jinsi kodi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='gender_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Jinsi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='group_education_lang_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name="Guruh ta'lim tili kodi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='group_education_lang_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="Guruh ta'lim tili"),
        ),
        migrations.AlterField(
            model_name='student',
            name='group_id_api',
            field=models.IntegerField(blank=True, null=True, verbose_name='Guruh ID (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='group_name_api',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Guruh nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='image_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='Talabning surati (URL)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='last_login_api',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Oxirgi kirish (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='last_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Familiyasi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='level_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Kurs kodi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='level_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Kurs nomi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='passport_number',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Pasport raqami'),
        ),
        migrations.AlterField(
            model_name='student',
            name='passport_pin',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Pasport PIN'),
        ),
        migrations.AlterField(
            model_name='student',
            name='password_is_valid_api',
            field=models.BooleanField(blank=True, null=True, verbose_name="Parol to'g'riligi (API)"),
        ),
        migrations.AlterField(
            model_name='student',
            name='patronymic',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Otasining ismi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='payment_form_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name="To'lov shakli kodi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='payment_form_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="To'lov shakli"),
        ),
        migrations.AlterField(
            model_name='student',
            name='phone',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Telefon raqami'),
        ),
        migrations.AlterField(
            model_name='student',
            name='province_code_api',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Viloyat kodi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='province_name_api',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Viloyat nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='semester_code_api',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Semestr kodi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='semester_education_year_code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name="Semestr o'quv yili kodi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='semester_education_year_is_current',
            field=models.BooleanField(blank=True, null=True, verbose_name="Joriy o'quv yili (semestr)"),
        ),
        migrations.AlterField(
            model_name='student',
            name='semester_education_year_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Semestr o'quv yili nomi"),
        ),
        migrations.AlterField(
            model_name='student',
            name='semester_id_api',
            field=models.IntegerField(blank=True, null=True, verbose_name='Semestr ID (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='semester_is_current',
            field=models.BooleanField(blank=True, null=True, verbose_name='Joriy semestr'),
        ),
        migrations.AlterField(
            model_name='student',
            name='semester_name_api',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Semestr nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='short_name_api',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Qisqa F.I.Sh. (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='social_category_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Ijtimoiy toifa kodi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='social_category_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Ijtimoiy toifa nomi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='specialty_code_api',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Mutaxassislik kodi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='specialty_id_api',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Mutaxassislik ID (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='specialty_name_api',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Mutaxassislik nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='student_id_number',
            field=models.CharField(blank=True, help_text='API dan olingan talabaning ID raqami', max_length=50, null=True, unique=True, verbose_name='Talaba ID raqami (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='student_status_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Talaba status kodi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='student_status_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Talaba statusi'),
        ),
        migrations.AlterField(
            model_name='student',
            name='university_name_api',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Universitet nomi (API)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqti'),
        ),
        migrations.AlterField(
            model_name='student',
            name='username',
            field=models.CharField(help_text='Tizimga kirish uchun foydalaniladigan login (Talaba ID raqami)', max_length=150, unique=True, verbose_name='Foydalanuvchi nomi (login)'),
        ),
        migrations.AlterField(
            model_name='student',
            name='validate_url_api',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='Validatsiya havolasi (API)'),
        ),
    ]
