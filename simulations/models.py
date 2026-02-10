"""
Simulation models - Runs, Responses, and Aggregates
"""
from django.db import models
from core.models import BaseModel
from projects.models import Project
from audiences.models import AudienceSegment, AgentProfile
from stimuli.models import Stimulus


class SimulationRun(BaseModel):
    """
    Represents one execution of a simulation across selected phases.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial (some errors)'),
    ]
    
    PHASE_CHOICES = [
        ('D1', 'Day 1'),
        ('D7', 'Day 7'),
        ('D30', 'Day 30'),
        ('D90', 'Day 90'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='simulation_runs')
    stimulus = models.ForeignKey(Stimulus, on_delete=models.CASCADE, related_name='simulation_runs')
    segment = models.ForeignKey(AudienceSegment, on_delete=models.CASCADE, related_name='simulation_runs')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    phases = models.JSONField(default=list, help_text="List of phases to run, e.g. ['D1', 'D7']")
    agent_count = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_summary = models.TextField(blank=True)
    error_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Run {self.id} - {self.stimulus.title} ({self.status})"


class AgentResponse(BaseModel):
    """
    Stores validated model output per agent per phase.
    """
    run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='responses')
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='responses')
    phase = models.CharField(max_length=10)
    
    # Structured output fields
    approval_score = models.IntegerField()
    emotions_json = models.JSONField(default=dict)
    intent_label = models.CharField(max_length=50)
    intent_confidence = models.FloatField()
    verbatim_text = models.TextField()
    
    # Raw output storage (optional)
    raw_json = models.JSONField(null=True, blank=True)
    
    # Processing metadata
    processing_time_ms = models.IntegerField(default=0)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['phase', 'agent__display_name']
        unique_together = ['run', 'agent', 'phase']
    
    def __str__(self):
        return f"{self.agent.display_name} - {self.phase} (approval: {self.approval_score})"


class RunAggregate(BaseModel):
    """
    Precomputed summary for fast result retrieval.
    One record per run per phase.
    """
    run = models.ForeignKey(SimulationRun, on_delete=models.CASCADE, related_name='aggregates')
    phase = models.CharField(max_length=10)
    
    # Aggregate metrics
    response_count = models.IntegerField(default=0)
    avg_approval = models.FloatField(default=0)
    approval_distribution = models.JSONField(default=dict, help_text="Counts per score bucket")
    emotion_means_json = models.JSONField(default=dict)
    intent_counts_json = models.JSONField(default=dict)
    top_themes_json = models.JSONField(default=list, help_text="Extracted themes from verbatims")
    representative_quotes = models.JSONField(default=list, help_text="Sample verbatims")
    
    class Meta:
        ordering = ['phase']
        unique_together = ['run', 'phase']
    
    def __str__(self):
        return f"Aggregate {self.run.id} - {self.phase}"