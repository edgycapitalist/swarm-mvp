from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'primary_language', 'owner', 'created_at']
    list_filter = ['region', 'primary_language', 'created_at']
    search_fields = ['name', 'description']