"""
Main URL configuration for SWARM MVP
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include([
        path('', include('projects.urls')),
        path('', include('audiences.urls')),
        path('', include('stimuli.urls')),
        path('', include('simulations.urls')),
    ])),
]