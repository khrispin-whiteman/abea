from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('pesapal/', include('django_pesapalv3.urls', namespace='django_pesapalv3')),
]

urlpatterns += i18n_patterns(
    path('', include('abea_app.urls')),
    path('accounts/', include('accounts_app.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)