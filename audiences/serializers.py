"""
Serializers for Audiences API
"""
from rest_framework import serializers
from .models import AudienceSegment, AgentProfile


class AgentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentProfile
        fields = ['id', 'display_name', 'traits_json', 'created_at']
        read_only_fields = ['id', 'created_at']


class AudienceSegmentSerializer(serializers.ModelSerializer):
    agent_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AudienceSegment
        fields = ['id', 'project', 'name', 'description', 
                  'demographics_json', 'style_guide_json', 
                  'attitudes_json', 'engagement_json',
                  'agent_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'agent_count', 'created_at', 'updated_at']
    
    def get_agent_count(self, obj):
        return obj.agents.count()


class GenerateAgentsSerializer(serializers.Serializer):
    """Serializer for agent generation request"""
    count = serializers.IntegerField(min_value=1, max_value=50, default=20)
    seed = serializers.IntegerField(required=False, allow_null=True)