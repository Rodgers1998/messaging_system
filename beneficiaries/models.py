# beneficiaries/models.py
from django.db import models

class Beneficiary(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    infobip_synced = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Auto-sync to Infobip only if not yet synced
        # Import here to avoid circular import (messaging.models → beneficiaries.models → messaging.utils)
        if not self.infobip_synced:
            try:
                from messaging.utils.infobip import sync_contact_to_infobip
                success, _ = sync_contact_to_infobip(self.name, self.phone_number)
                self.infobip_synced = bool(success)  # returns (True/False, data)
            except Exception:
                self.infobip_synced = False  # don't block saving if sync fails
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"