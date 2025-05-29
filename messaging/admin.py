from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'channel', 'status', 'sent_at', 'message_sid')
    list_filter = ('channel', 'status', 'sent_at')
    search_fields = ('recipient__phone_number', 'content', 'message_sid')
    ordering = ('-sent_at',)
