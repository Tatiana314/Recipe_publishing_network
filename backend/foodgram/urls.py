"""
Конфигурация URL-адреса для проекта foodgram.

Список `urlpatterns` направляет URL-адреса в представления.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]
