# beneficiaries/admin.py
from django.contrib import admin, messages
from import_export.admin import ImportExportMixin
from import_export import resources
from .models import Beneficiary

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
        from messaging.utils.infobip import sync_contact_to_infobip
        synced = 0
        failed = 0

        for beneficiary in queryset:
            if beneficiary.infobip_synced:
                continue
            success, _ = sync_contact_to_infobip(beneficiary.name, beneficiary.phone_number)
            # sync_contact_to_infobip returns (bool, data) — not (status_code, data)
            if success:
                beneficiary.infobip_synced = True
                beneficiary.save(update_fields=['infobip_synced'])
                synced += 1
            else:
                failed += 1

        self.message_user(
            request,
            f"{synced} beneficiaries synced, {failed} failed.",
            level=messages.SUCCESS if failed == 0 else messages.WARNING
        )
    sync_to_infobip.short_description = "Sync selected beneficiaries to Infobip"