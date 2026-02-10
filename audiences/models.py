"""
Audience models - Segments and Agent Profiles
"""
from django.db import models
from core.models import BaseModel
from projects.models import Project


class AudienceSegment(BaseModel):
    """
    Defines a segment template used to generate agents.
    Contains demographics, style guide, attitudes, and engagement patterns.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='segments')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # JSON fields for flexible schema iteration
    demographics_json = models.JSONField(default=dict, help_text="Age range, gender split, location, income, education")
    style_guide_json = models.JSONField(default=dict, help_text="Communication style, formality, emoji usage, dialect")
    attitudes_json = models.JSONField(default=dict, help_text="Attitudes toward key topics, brands, values")
    engagement_json = models.JSONField(default=dict, help_text="Platform preferences, posting frequency, influence level")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.project.name})"


class AgentProfile(BaseModel):
    """
    Individual audience member with specific traits and memory.
    Generated from a segment template.
    """
    segment = models.ForeignKey(AudienceSegment, on_delete=models.CASCADE, related_name='agents')
    display_name = models.CharField(max_length=100)
    
    # Agent-specific traits (instantiated from segment template with variation)
    traits_json = models.JSONField(default=dict, help_text="Specific demographics, personality, values")
    
    # Rolling memory for multi-phase simulations
    memory_text = models.TextField(blank=True, help_text="Agent's memory from previous phases")
    
    class Meta:
        ordering = ['display_name']
    
    def __str__(self):
        return f"{self.display_name} ({self.segment.name})"