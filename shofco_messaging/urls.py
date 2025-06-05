from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),  # Dashboard app urls
    path('messaging/', include(('messaging.urls', 'messaging'), namespace='messaging')),

    path("survey/", include("surveys.urls", namespace="surveys")),
    path('', lambda request: redirect('messaging/', permanent=False)),  # 👈 this line fixes it
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)