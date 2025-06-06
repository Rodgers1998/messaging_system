# beneficiaries/admin.py
from django.contrib import admin, messages
from import_export.admin import ImportExportMixin
from import_export import resources
from .models import Beneficiary
from messaging.utils.infobip import sync_contact_to_infobip 

class BeneficiaryResource(resources.ModelResource):
    class Meta:
        model = Beneficiary
        fields = ('id', 'name', 'phone_number', 'email', 'infobip_synced')

@admin.register(Beneficiary)
class BeneficiaryAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = BeneficiaryResource
    list_display = ('name', 'phone_number', 'email', 'infobip_synced')
    list_filter = ('infobip_synced',)
    search_fields = ('name', 'phone_number', 'email')
    actions = ['sync_to_infobip']

    def sync_to_infobip(self, request, queryset):
        synced = 0
        failed = 0

        for beneficiary in queryset:
            if beneficiary.infobip_synced:
                continue
            status, _ = sync_contact_to_infobip(beneficiary.name, beneficiary.phone_number)
            if 200 <= status < 300:
                beneficiary.infobip_synced = True
                beneficiary.save()
                synced += 1
            else:
                failed += 1

        self.message_user(
            request,
            f"{synced} beneficiaries synced, {failed} failed.",
            level=messages.SUCCESS if failed == 0 else messages.WARNING
        )
    sync_to_infobip.short_description = "Sync selected beneficiaries to Infobip"
