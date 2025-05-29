from messaging.models import Message
from messaging.utils.infobip import send_sms_via_infobip, send_whatsapp_via_infobip
from messaging.utils.email_utils import send_email_message  # ✅ You’ll create this
from django.utils import timezone

def send_message(message: Message):
    phone_number = message.recipient.phone_number
    content = message.content

    if message.channel.upper() == "SMS":
        success, result = send_sms_via_infobip(phone_number, content)
    elif message.channel.upper() == "WHATSAPP":
        success, result = send_whatsapp_via_infobip(phone_number, content)
    elif message.channel.upper() == "EMAIL":
        recipient_email = message.recipient.email
        if not recipient_email:
            success, result = False, "Missing recipient email"
        else:
            success, result = send_email_message(recipient_email, content)
    else:
        success, result = False, "Unsupported channel"

    if success:
        message.status = "SENT"
        message.sent_at = timezone.now()
        message.message_sid = result
    else:
        message.status = "FAILED"
        message.message_sid = result

    message.save()
