from django.contrib import admin
from .models import AudienceSegment, AgentProfile


@admin.register(AudienceSegment)
class AudienceSegmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'created_at']
    list_filter = ['project', 'created_at']
    search_fields = ['name', 'description']


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'segment', 'created_at']
    list_filter = ['segment', 'created_at']
    search_fields = ['display_name']