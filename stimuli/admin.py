from django.contrib import admin
from .models import Stimulus


@admin.register(Stimulus)
class StimulusAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'channel', 'scenario_tag', 'created_at']
    list_filter = ['channel', 'scenario_tag', 'project', 'created_at']
    search_fields = ['title', 'message_text']