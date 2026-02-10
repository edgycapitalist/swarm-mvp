"""
Serializers for Simulations API
"""
from rest_framework import serializers
from .models import SimulationRun, AgentResponse, RunAggregate


class AgentResponseSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.display_name', read_only=True)
    
    class Meta:
        model = AgentResponse
        fields = ['id', 'agent', 'agent_name', 'phase', 'approval_score',
                  'emotions_json', 'intent_label', 'intent_confidence',
                  'verbatim_text', 'processing_time_ms', 'created_at']


class RunAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunAggregate
        fields = ['phase', 'response_count', 'avg_approval', 'approval_distribution',
                  'emotion_means_json', 'intent_counts_json', 'top_themes_json',
                  'representative_quotes', 'generated_at']


class SimulationRunSerializer(serializers.ModelSerializer):
    stimulus_title = serializers.CharField(source='stimulus.title', read_only=True)
    segment_name = serializers.CharField(source='segment.name', read_only=True)
    
    class Meta:
        model = SimulationRun
        fields = ['id', 'project', 'stimulus', 'stimulus_title', 'segment', 'segment_name',
                  'status', 'phases', 'agent_count', 'started_at', 'completed_at',
                  'error_count', 'error_summary', 'created_at']
        read_only_fields = ['id', 'status', 'agent_count', 'started_at', 'completed_at',
                           'error_count', 'error_summary', 'created_at']


class CreateSimulationSerializer(serializers.Serializer):
    """Serializer for creating and running a simulation"""
    stimulus_id = serializers.UUIDField()
    segment_id = serializers.UUIDField()
    phases = serializers.ListField(
        child=serializers.ChoiceField(choices=['D1', 'D7', 'D30', 'D90']),
        default=['D1', 'D7']
    )


class SimulationResultsSerializer(serializers.Serializer):
    """Serializer for simulation results response"""
    run = SimulationRunSerializer()
    aggregates = RunAggregateSerializer(many=True)
    responses = AgentResponseSerializer(many=True, required=False)