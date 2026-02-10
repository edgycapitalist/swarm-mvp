"""
Project model - top-level container for audiences, stimuli, and runs
"""
from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class Project(BaseModel):
    """A project groups related audiences, stimuli, and simulation runs"""
    
    REGION_CHOICES = [
        ('MENA', 'Middle East & North Africa'),
        ('GCC', 'Gulf Cooperation Council'),
        ('SA', 'Saudi Arabia'),
        ('AE', 'United Arab Emirates'),
        ('EG', 'Egypt'),
        ('GLOBAL', 'Global'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('ar-sa', 'Arabic (Saudi)'),
        ('ar-eg', 'Arabic (Egyptian)'),
        ('ar-ae', 'Arabic (Emirati)'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    region = models.CharField(max_length=20, choices=REGION_CHOICES, default='MENA')
    primary_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name