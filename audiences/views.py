"""
API views for Audiences
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from .models import AudienceSegment, AgentProfile
from .serializers import (
    AudienceSegmentSerializer, 
    AgentProfileSerializer,
    GenerateAgentsSerializer
)
from .generators import generate_agents_for_segment


class AudienceSegmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for audience segments.
    """
    serializer_class = AudienceSegmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter segments by project and user ownership"""
        queryset = AudienceSegment.objects.filter(project__owner=self.request.user)
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def generate_agents(self, request, pk=None):
        """
        Generate agent profiles from this segment template.
        
        POST /api/segments/{id}/generate_agents/
        Body: {"count": 20, "seed": 42}
        """
        segment = self.get_object()
        
        # Validate request
        serializer = GenerateAgentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        count = serializer.validated_data['count']
        seed = serializer.validated_data.get('seed')
        
        # Check max agents limit
        if count > settings.SIM_MAX_AGENTS:
            return Response(
                {'error': f'Maximum {settings.SIM_MAX_AGENTS} agents allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate agents
        agents = generate_agents_for_segment(segment, count=count, seed=seed)
        
        # Return created agents
        return Response({
            'message': f'Created {len(agents)} agents',
            'agents': AgentProfileSerializer(agents, many=True).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def agents(self, request, pk=None):
        """
        List all agents in this segment.
        
        GET /api/segments/{id}/agents/
        """
        segment = self.get_object()
        agents = segment.agents.all()
        serializer = AgentProfileSerializer(agents, many=True)
        return Response(serializer.data)


class AgentProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for agent profiles (read-only).
    Agents are created via segment.generate_agents()
    """
    serializer_class = AgentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AgentProfile.objects.filter(
            segment__project__owner=self.request.user
        )