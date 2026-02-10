"""
API views for Stimuli
"""
from rest_framework import viewsets, permissions
from .models import Stimulus
from .serializers import StimulusSerializer


class StimulusViewSet(viewsets.ModelViewSet):
    """
    API endpoint for stimuli (messages to test).
    """
    serializer_class = StimulusSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter stimuli by project and user ownership"""
        queryset = Stimulus.objects.filter(project__owner=self.request.user)
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset