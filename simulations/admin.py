from django.contrib import admin
from .models import SimulationRun, AgentResponse, RunAggregate


@admin.register(SimulationRun)
class SimulationRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'stimulus', 'segment', 'status', 'agent_count', 'created_at']
    list_filter = ['status', 'project', 'created_at']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(AgentResponse)
class AgentResponseAdmin(admin.ModelAdmin):
    list_display = ['agent', 'run', 'phase', 'approval_score', 'intent_label']
    list_filter = ['phase', 'intent_label', 'run']


@admin.register(RunAggregate)
class RunAggregateAdmin(admin.ModelAdmin):
    list_display = ['run', 'phase', 'response_count', 'avg_approval']
    list_filter = ['phase']