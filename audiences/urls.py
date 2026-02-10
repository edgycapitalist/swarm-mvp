"""
URL routing for Audiences API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AudienceSegmentViewSet, AgentProfileViewSet

router = DefaultRouter()
router.register(r'segments', AudienceSegmentViewSet, basename='segment')
router.register(r'agents', AgentProfileViewSet, basename='agent')

urlpatterns = [
    path('', include(router.urls)),
]