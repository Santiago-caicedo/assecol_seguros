
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/cuentas/login/', permanent=False), name='inicio'),
    path('admin/', admin.site.urls),
    path('cuentas/', include('django.contrib.auth.urls')),
    path('', include('usuarios.urls')),
    #path('polizas/', include('polizas.urls')),
    path('dashboard/', include('dashboard_admin.urls', namespace='dashboard_admin')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)