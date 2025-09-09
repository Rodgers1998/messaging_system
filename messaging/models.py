# messaging/models.py
from django.db import models
from django.utils import timezone
from beneficiaries.models import Beneficiary

class Message(models.Model):
    CHANNEL_CHOICES = [
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
    ]

    recipient = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    content = models.TextField()
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    message_sid = models.CharField(max_length=64, null=True, blank=True)

    # ✅ Option 1: Uploaded file
    media = models.FileField(upload_to="message_media/", null=True, blank=True)
    # ✅ Option 2: Direct URL
    media_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.recipient} - {self.channel} - {self.status}"

    def get_media_url(self):
        """
        Always return a public URL if available.
        - Prefer `media_url` if set.
        - Otherwise fallback to uploaded file URL.
        """
        if self.media_url:
            return self.media_url
        if self.media:
            try:
                return self.media.url  # Requires MEDIA_URL configured
            except Exception:
                return None
        return None
