from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0010_remove_private_student_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=150, unique=True, verbose_name='Login (HEMIS)')),
                ('hemis_id', models.CharField(blank=True, max_length=100, null=True, unique=True, verbose_name='HEMIS ID')),
                ('first_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Ismi')),
                ('last_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Familiyasi')),
                ('patronymic', models.CharField(blank=True, max_length=100, null=True, verbose_name="Otasining ismi")),
                ('full_name_api', models.CharField(blank=True, max_length=255, null=True, verbose_name="To'liq F.I.Sh. (API)")),
                ('image_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='Surat (URL)')),
                ('position', models.CharField(blank=True, max_length=255, null=True, verbose_name='Lavozimi')),
                ('department_name', models.CharField(blank=True, max_length=255, null=True, verbose_name="Bo'lim nomi")),
                ('department_code', models.CharField(blank=True, max_length=50, null=True, verbose_name="Bo'lim kodi")),
                ('phone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefon')),
                ('email', models.EmailField(blank=True, null=True, verbose_name='Email')),
                ('last_login_api', models.DateTimeField(blank=True, null=True, verbose_name='Oxirgi kirish (API)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqti')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqti')),
            ],
            options={
                'verbose_name': 'Hodim (API)',
                'verbose_name_plural': 'Hodimlar (API)',
                'ordering': ['-updated_at', 'last_name', 'first_name'],
            },
        ),
    ]
