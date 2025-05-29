from django.db import models
from django.utils import timezone
from beneficiaries.models import Beneficiary

class Message(models.Model):
    CHANNEL_CHOICES = [('SMS', 'SMS'), ('WHATSAPP', 'WhatsApp'), ('EMAIL', 'Email')]

    recipient = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    content = models.TextField()
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)  # new field
    message_sid = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return f"{self.recipient} - {self.channel} - {self.status}"
