"""
Serializers for Stimuli API
"""
from rest_framework import serializers
from .models import Stimulus


class StimulusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stimulus
        fields = ['id', 'project', 'title', 'channel', 'scenario_tag',
                  'context_text', 'message_text', 'sender_name', 'target_action',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']