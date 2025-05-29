from django.contrib import admin
from .models import Beneficiary

@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number')  # Adjust fields as per your model
    search_fields = ('name', 'phone_number')
