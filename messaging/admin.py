from django.contrib import admin
from django.utils.html import format_html
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'recipient',
        'channel',
        'status',
        'sent_at',
        'scheduled_for',
        'message_sid',
        'media_preview',
    )
    list_filter = ('channel', 'status', 'sent_at', 'scheduled_for')
    search_fields = ('recipient__phone_number', 'recipient__name', 'content', 'message_sid')
    ordering = ('-sent_at',)

    def media_preview(self, obj):
        """Show a preview/download link for media files in admin."""
        if obj.media:
            return format_html("<a href='{}' target='_blank'>View</a>", obj.media.url)
        return "-"
    media_preview.short_description = "Media"
