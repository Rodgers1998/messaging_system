# beneficiaries/models.py
from django.db import models

class Beneficiary(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)  # Add this field if missing
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name
