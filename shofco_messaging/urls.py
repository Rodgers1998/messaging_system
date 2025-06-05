from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views

from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('messaging/', include(('messaging.urls', 'messaging'), namespace='messaging')),
    path('survey/', include("surveys.urls", namespace="surveys")),
    
     # 👇 Add this line to redirect Django's default login to your custom one
    path('accounts/login/', lambda request: redirect('messaging:login')),

    # Optional: redirect root URL to messaging
    path('', lambda request: redirect('messaging/', permanent=False)),
    
]
