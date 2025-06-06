# beneficiaries/models.py
from django.db import models
from messaging.utils.infobip import sync_contact_to_infobip 

class Beneficiary(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    infobip_synced = models.BooleanField(default=False)  # New field

    def save(self, *args, **kwargs):
        # Auto-sync to Infobip only if not yet synced
        if not self.infobip_synced:
            status, _ = sync_contact_to_infobip(self.name, self.phone_number)
            self.infobip_synced = 200 <= status < 300
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"
