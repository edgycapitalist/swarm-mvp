"""
API views for Projects
"""
from rest_framework import viewsets, permissions
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for projects.
    
    list: Get all projects for the current user
    create: Create a new project
    retrieve: Get a specific project
    update: Update a project
    destroy: Delete a project
    """
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return projects owned by the current user"""
        return Project.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        """Set the owner to the current user"""
        serializer.save(owner=self.request.user)