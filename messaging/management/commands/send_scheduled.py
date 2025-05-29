from django.core.management.base import BaseCommand
from messaging.models import Message
from messaging.services.messaging_service import send_message
from django.utils import timezone

class Command(BaseCommand):
    help = 'Send scheduled messages that are due'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        scheduled_messages = Message.objects.filter(status='PENDING', scheduled_for__lte=now)
        for msg in scheduled_messages:
            send_message(msg)
            self.stdout.write(f"Sent message {msg.id} to {msg.recipient}")
