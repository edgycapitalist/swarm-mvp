"""
API views for Simulations
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from stimuli.models import Stimulus
from audiences.models import AudienceSegment
from .models import SimulationRun, AgentResponse, RunAggregate
from .serializers import (
    SimulationRunSerializer,
    CreateSimulationSerializer,
    RunAggregateSerializer,
    AgentResponseSerializer
)
from .orchestrator import run_simulation


class SimulationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for simulations.
    """
    serializer_class = SimulationRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter runs by project and user ownership"""
        queryset = SimulationRun.objects.filter(project__owner=self.request.user)
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('stimulus', 'segment')
    
    def create(self, request, *args, **kwargs):
        """
        Create and execute a new simulation run.
        
        POST /api/simulations/
        Body: {
            "stimulus_id": "uuid",
            "segment_id": "uuid",
            "phases": ["D1", "D7"]
        }
        """
        serializer = CreateSimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get stimulus and segment
        stimulus = get_object_or_404(
            Stimulus,
            id=serializer.validated_data['stimulus_id'],
            project__owner=request.user
        )
        segment = get_object_or_404(
            AudienceSegment,
            id=serializer.validated_data['segment_id'],
            project__owner=request.user
        )
        
        # Check they're in the same project
        if stimulus.project_id != segment.project_id:
            return Response(
                {'error': 'Stimulus and segment must be in the same project'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check segment has agents
        if not segment.agents.exists():
            return Response(
                {'error': 'Segment has no agents. Generate agents first using POST /api/segments/{id}/generate_agents/'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the run
        run = SimulationRun.objects.create(
            project=stimulus.project,
            stimulus=stimulus,
            segment=segment,
            phases=serializer.validated_data['phases'],
            status='pending'
        )
        
        # Execute synchronously (MVP)
        # TODO: Move to background task for larger runs
        try:
            run = run_simulation(run)
        except Exception as e:
            return Response(
                {'error': str(e), 'run_id': str(run.id)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            SimulationRunSerializer(run).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Get simulation results with aggregates.
        
        GET /api/simulations/{id}/results/
        Optional query params:
        - phase: Filter by phase (D1, D7, etc.)
        - include_responses: Include individual agent responses (default: false)
        """
        run = self.get_object()
        
        # Get aggregates
        aggregates = run.aggregates.all()
        phase = request.query_params.get('phase')
        if phase:
            aggregates = aggregates.filter(phase=phase)
        
        result = {
            'run': SimulationRunSerializer(run).data,
            'aggregates': RunAggregateSerializer(aggregates, many=True).data,
        }
        
        # Optionally include individual responses
        if request.query_params.get('include_responses', '').lower() == 'true':
            responses = run.responses.all()
            if phase:
                responses = responses.filter(phase=phase)
            result['responses'] = AgentResponseSerializer(responses, many=True).data
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """
        Export simulation results as CSV.
        
        GET /api/simulations/{id}/export/
        """
        run = self.get_object()
        
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="simulation_{run.id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Phase', 'Agent', 'Approval', 'Intent', 'Intent Confidence',
            'Joy', 'Trust', 'Fear', 'Surprise', 'Sadness', 'Disgust', 'Anger', 'Anticipation',
            'Verbatim'
        ])
        
        for resp in run.responses.all().select_related('agent'):
            emotions = resp.emotions_json or {}
            writer.writerow([
                resp.phase,
                resp.agent.display_name,
                resp.approval_score,
                resp.intent_label,
                resp.intent_confidence,
                emotions.get('joy', 0),
                emotions.get('trust', 0),
                emotions.get('fear', 0),
                emotions.get('surprise', 0),
                emotions.get('sadness', 0),
                emotions.get('disgust', 0),
                emotions.get('anger', 0),
                emotions.get('anticipation', 0),
                resp.verbatim_text
            ])
        
        return response