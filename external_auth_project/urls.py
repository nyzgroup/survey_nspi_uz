from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language

from auth_app.media_views import protected_media_staff_or_student

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/set_language/', set_language, name='set_language'),
    path('', include('auth_app.urls')),
    # Media — autentifikatsiyasiz ochiq emas (FIND-009)
    re_path(r'^media/(?P<path>.*)$', protected_media_staff_or_student, name='protected_media'),
]

# Static (dev): WhiteNoise productionda STATIC_ROOT ni xizmat qiladi
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
