"""
Stimulus model - the message/content being tested
"""
from django.db import models
from core.models import BaseModel
from projects.models import Project


class Stimulus(BaseModel):
    """
    The message being tested plus scenario context.
    """
    
    CHANNEL_CHOICES = [
        ('social_twitter', 'Social Media - Twitter/X'),
        ('social_instagram', 'Social Media - Instagram'),
        ('social_tiktok', 'Social Media - TikTok'),
        ('social_linkedin', 'Social Media - LinkedIn'),
        ('press_release', 'Press Release'),
        ('news_article', 'News Article'),
        ('ad_digital', 'Digital Advertisement'),
        ('ad_tv', 'TV Advertisement'),
        ('email', 'Email'),
        ('internal_memo', 'Internal Memo'),
        ('policy_announcement', 'Policy Announcement'),
        ('other', 'Other'),
    ]
    
    SCENARIO_CHOICES = [
        ('product_launch', 'Product Launch'),
        ('campaign', 'Marketing Campaign'),
        ('crisis', 'Crisis Response'),
        ('policy', 'Policy Announcement'),
        ('rebrand', 'Rebranding'),
        ('csr', 'CSR Initiative'),
        ('earnings', 'Earnings/Financial'),
        ('leadership', 'Leadership Change'),
        ('other', 'Other'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stimuli')
    title = models.CharField(max_length=255)
    channel = models.CharField(max_length=50, choices=CHANNEL_CHOICES)
    scenario_tag = models.CharField(max_length=50, choices=SCENARIO_CHOICES)
    
    # The actual content
    context_text = models.TextField(help_text="Background context for the scenario")
    message_text = models.TextField(help_text="The actual message being tested")
    
    # Optional metadata
    sender_name = models.CharField(max_length=255, blank=True, help_text="Who is sending this message")
    target_action = models.CharField(max_length=255, blank=True, help_text="What action do we want audience to take")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stimuli'
    
    def __str__(self):
        return f"{self.title} ({self.scenario_tag})"