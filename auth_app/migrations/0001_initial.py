# Generated by Django 4.2.20 on 2025-05-25 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_user_id', models.CharField(blank=True, help_text="Tashqi API dagi foydalanuvchi uchun unikal ID (agar mavjud bo'lsa)", max_length=255, null=True, unique=True)),
                ('student_id_number', models.CharField(blank=True, help_text='Talabaning unikal ID raqami (API dan)', max_length=50, null=True, unique=True)),
                ('username', models.CharField(help_text='Tizimga kirish uchun foydalaniladigan login', max_length=150, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(blank=True, max_length=100, null=True)),
                ('patronymic', models.CharField(blank=True, max_length=100, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('faculty', models.CharField(blank=True, max_length=200, null=True)),
                ('course', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('group_name', models.CharField(blank=True, max_length=50, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('last_login_api', models.DateTimeField(blank=True, help_text='API orqali oxirgi muvaffaqiyatli kirish vaqti', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Talaba',
                'verbose_name_plural': 'Talabalar',
                'ordering': ['last_name', 'first_name'],
            },
        ),
    ]
