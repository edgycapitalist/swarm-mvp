"""
URL routing for Stimuli API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StimulusViewSet

router = DefaultRouter()
router.register(r'stimuli', StimulusViewSet, basename='stimulus')

urlpatterns = [
    path('', include(router.urls)),
]