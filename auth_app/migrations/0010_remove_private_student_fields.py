from django.db import migrations


class Migration(migrations.Migration):
    """
    Talabalarning o'ta shaxsiy ma'lumotlarini (pasport, telefon, email,
    manzil, ijtimoiy holat, turar joy) Student modelidan olib tashlaydi.
    Bu ma'lumotlar HEMIS API dan olinmaydi va saqlanmaydi.
    """

    dependencies = [
        ('auth_app', '0009_messagetoresponsible_qr_code_image_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='passport_pin',
        ),
        migrations.RemoveField(
            model_name='student',
            name='passport_number',
        ),
        migrations.RemoveField(
            model_name='student',
            name='birth_date_timestamp',
        ),
        migrations.RemoveField(
            model_name='student',
            name='address_api',
        ),
        migrations.RemoveField(
            model_name='student',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='student',
            name='email',
        ),
        migrations.RemoveField(
            model_name='student',
            name='social_category_code',
        ),
        migrations.RemoveField(
            model_name='student',
            name='social_category_name',
        ),
        migrations.RemoveField(
            model_name='student',
            name='accommodation_code',
        ),
        migrations.RemoveField(
            model_name='student',
            name='accommodation_name',
        ),
        migrations.RemoveField(
            model_name='student',
            name='validate_url_api',
        ),
        migrations.RemoveField(
            model_name='student',
            name='password_is_valid_api',
        ),
    ]
