# messaging/utils/infobip.py
import os
import requests
import mimetypes
import logging
from dotenv import load_dotenv

load_dotenv()

# ---------------- Environment ---------------- #
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL", "").rstrip("/")
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_SENDER_SMS = os.getenv("INFOBIP_SENDER_SMS", "SHOFCO")
INFOBIP_SENDER_WHATSAPP = os.getenv("INFOBIP_SENDER_WHATSAPP", "")

# ---------------- Logger ---------------- #
logger = logging.getLogger(__name__)


# ---------------- Helpers ---------------- #
def _replace_placeholders(text: str, parameters: dict = None) -> str:
    if parameters:
        for k, v in parameters.items():
            text = text.replace(f"{{{{{k}}}}}", str(v))
    return text


def _format_phone(to_phone: str) -> str:
    """
    Normalize phone to E.164 format.
    Handles: 0712345678, 254712345678, +254712345678
    """
    to_phone = str(to_phone).strip().replace(" ", "").replace("-", "")
    if to_phone.startswith("+"):
        return to_phone
    if to_phone.startswith("0"):
        return "+254" + to_phone[1:]
    if to_phone.startswith("254"):
        return "+" + to_phone
    return "+" + to_phone  # fallback: assume missing +


def _get_whatsapp_sender() -> str:
    """Return the WhatsApp sender number, ensuring it has no + (Infobip requires no + for sender)."""
    sender = INFOBIP_SENDER_WHATSAPP.strip()
    # Infobip sender should NOT have + prefix
    return sender.lstrip("+")


def _post_request(url: str, payload: dict):
    """Unified POST to Infobip with logging."""
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    logger.info("Infobip POST → %s | payload: %s", url, payload)
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        try:
            data = response.json()
        except ValueError:
            data = {"error": "Invalid JSON response", "raw": response.text}

        logger.info("Infobip [%s] ← %s", response.status_code, data)

        if response.status_code in [200, 201]:
            return True, data
        return False, data

    except Exception as e:
        logger.exception("Infobip request failed: %s", str(e))
        return False, {"error": str(e)}


# ---------------- SMS ---------------- #
def send_sms_via_infobip(to_phone: str, message_text: str, parameters: dict = None):
    """Send SMS via Infobip."""
    message_text = _replace_placeholders(message_text, parameters)
    to_phone = _format_phone(to_phone)

    url = f"{INFOBIP_BASE_URL}/sms/2/text/advanced"
    payload = {
        "messages": [
            {
                "from": INFOBIP_SENDER_SMS,
                "destinations": [{"to": to_phone}],
                "text": message_text,
            }
        ]
    }
    return _post_request(url, payload)


# ---------------- WhatsApp Text ---------------- #
def send_whatsapp_via_infobip(to_phone: str, message_text: str, parameters: dict = None):
    """
    Send plain text WhatsApp message via Infobip.
    Correct payload: { from, to, content: { text } }  — NO 'type' field inside content.
    """
    message_text = _replace_placeholders(message_text, parameters)
    to_phone = _format_phone(to_phone)
    sender = _get_whatsapp_sender()

    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/text"
    payload = {
        "from": sender,
        "to": to_phone,
        "content": {
            "text": message_text   # ✅ No "type" field — Infobip rejects it
        },
    }
    return _post_request(url, payload)


# ---------------- WhatsApp Media ---------------- #
def send_whatsapp_media_via_infobip(to_phone: str, media_url: str, caption: str = ""):
    """
    Send WhatsApp media message via Infobip.
    media_url must be publicly accessible.
    """
    caption = (caption or "").strip()
    if len(caption) > 1024:
        caption = caption[:1021] + "..."

    to_phone = _format_phone(to_phone)
    sender = _get_whatsapp_sender()

    # Detect media type from URL
    mime_type, _ = mimetypes.guess_type(media_url)
    media_type = "image"  # default
    if mime_type:
        if mime_type.startswith("video"):
            media_type = "video"
        elif mime_type.startswith("audio"):
            media_type = "audio"
        elif mime_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            media_type = "document"

    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/image"  # ✅ Use type-specific endpoint
    if media_type != "image":
        url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/{media_type}"

    payload = {
        "from": sender,
        "to": to_phone,
        "content": {
            "mediaUrl": media_url,
            "caption": caption,
        },
    }
    return _post_request(url, payload)


# ---------------- Contacts Sync ---------------- #
def sync_contact_to_infobip(name: str, phone_number: str):
    """Register or update a contact in Infobip People."""
    phone_number = _format_phone(phone_number)
    url = f"{INFOBIP_BASE_URL}/people/2/persons"
    payload = {"firstName": name, "phoneNumbers": [phone_number]}
    return _post_request(url, payload)