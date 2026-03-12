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

    # Increased from 64 — Infobip bulkId / messageId can exceed 64 chars
    message_sid = models.CharField(max_length=255, null=True, blank=True)

    # Uploaded file (kept for admin preview — not used for sending)
    media = models.FileField(upload_to="message_media/", null=True, blank=True)
    # Public Cloudinary URL — this is what Infobip fetches
    media_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.recipient} - {self.channel} - {self.status}"

    def get_media_url(self):
        """Return public URL for media. Prefers media_url (Cloudinary) over local file."""
        if self.media_url:
            return self.media_url
        if self.media:
            try:
                return self.media.url
            except Exception:
                return None
        return None