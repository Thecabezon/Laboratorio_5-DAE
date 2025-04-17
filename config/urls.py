from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventory/', include('inventory.urls')),
    path('', RedirectView.as_view(url='/inventory/', permanent=False)),  # <--- ESTA LÍNEA
    path('circulation/', include('circulation.urls')),
    path('', lambda request: redirect('circulation/')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

