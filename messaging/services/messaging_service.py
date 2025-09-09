# messaging/services/messaging_service.py
import logging
from django.utils import timezone
from messaging.models import Message
from messaging.utils.infobip import (
    send_sms_via_infobip,
    send_whatsapp_via_infobip,
    send_whatsapp_media_via_infobip,
)
from messaging.utils.email_utils import send_email_message

logger = logging.getLogger(__name__)


def send_message(message: Message, parameters: dict = None):
    """
    Send a message via SMS, WhatsApp, or Email.
    - Prefers a public media URL (message.get_media_url()) for WhatsApp media.
    - Injects recipient name into parameters as {{1}} if not provided.
    - Returns (success: bool, result: dict|str)
    """
    channel = (message.channel or "").upper()
    phone_number = getattr(message.recipient, "phone_number", None)

    # Check phone number availability
    if channel in ("SMS", "WHATSAPP") and not phone_number:
        error_msg = "Recipient missing phone number"
        logger.error(error_msg)
        _update_message_status(message, success=False, result=error_msg)
        return False, error_msg

    content = message.content or ""

    # Prefer media_url → fallback to uploaded media file
    try:
        media_url = message.get_media_url() if hasattr(message, "get_media_url") else None
    except Exception as e:
        logger.debug("Could not determine media URL for message %s: %s", message.id, e)
        media_url = None

    # Always include recipient name in template params
    parameters = parameters or {}
    if "1" not in parameters:
        parameters["1"] = getattr(message.recipient, "name", "")

    success, result = False, None

    try:
        if channel == "SMS":
            success, result = send_sms_via_infobip(phone_number, content, parameters)

        elif channel == "WHATSAPP":
            if media_url:
                # Send media message with caption
                success, result = send_whatsapp_media_via_infobip(
                    phone_number, media_url=media_url, caption=content
                )
            else:
                # Send plain WhatsApp text
                success, result = send_whatsapp_via_infobip(
                    phone_number, content, parameters
                )

        elif channel == "EMAIL":
            recipient_email = getattr(message.recipient, "email", None)
            if not recipient_email:
                success, result = False, "Missing recipient email"
            else:
                success, result = send_email_message(recipient_email, content)

        else:
            success, result = False, f"Unsupported channel: {message.channel}"

    except Exception as e:
        success, result = False, f"Exception while sending: {str(e)}"
        logger.exception(
            "Exception when sending message %s via %s", message.id, message.channel
        )

    # Persist status + message SID
    _update_message_status(message, success, result)
    return success, result


def _extract_message_id_from_result(result):
    """
    Try to pull a sensible message id string from the API result.
    Supports Infobip's typical response structures.
    """
    if result is None:
        return ""
    if isinstance(result, (str, int)):
        return str(result)

    if isinstance(result, dict):
        # Common Infobip response shapes
        msg_id = result.get("messageId")
        if not msg_id:
            messages_list = result.get("messages")
            if isinstance(messages_list, list) and messages_list:
                msg_id = (
                    messages_list[0].get("messageId")
                    if isinstance(messages_list[0], dict)
                    else None
                )
        return str(msg_id) if msg_id else str(result)

    return str(result)


def _update_message_status(message: Message, success: bool, result):
    """
    Update the message model with the send result.
    Only updates status, sent_at and message_sid.
    """
    message.status = "SENT" if success else "FAILED"
    message.sent_at = timezone.now() if success else None

    try:
        message.message_sid = _extract_message_id_from_result(result)
    except Exception as e:
        logger.debug(
            "Could not extract message id for message %s: %s",
            getattr(message, "id", "n/a"),
            e,
        )
        message.message_sid = str(result)

    try:
        message.save(update_fields=["status", "sent_at", "message_sid"])
    except Exception:
        # Fallback if update_fields fails
        message.save()

    logger.info(
        "Message %s updated: status=%s, sid=%s",
        getattr(message, "id", "n/a"),
        message.status,
        message.message_sid,
    )
