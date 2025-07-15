from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect  # Add this

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('login/')),  # Redirect empty path to login
    path('', include('core.urls')),
]
