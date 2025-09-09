# messaging/services/infobip_service.py
import os
import requests
import mimetypes
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- Environment ---------------- #
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")  # e.g. https://xxxx.api.infobip.com
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_SENDER_SMS = os.getenv("INFOBIP_SENDER_SMS", "SHOFCO")
INFOBIP_SENDER_WHATSAPP = os.getenv("INFOBIP_SENDER_WHATSAPP")

# ---------------- Logger ---------------- #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ---------------- Helpers ---------------- #
def _replace_placeholders(text: str, parameters: dict = None) -> str:
    """Replace placeholders like {{1}}, {{2}} in the text using parameters dict."""
    if parameters:
        for k, v in parameters.items():
            text = text.replace(f"{{{{{k}}}}}", str(v))
    return text


def _format_phone(to_phone: str) -> str:
    """
    Ensure phone number is in E.164 format for Infobip/WhatsApp.
    - 0712345678 -> +254712345678
    - 254712345678 -> +254712345678
    - +254712345678 -> stays the same
    """
    to_phone = str(to_phone).strip()
    if to_phone.startswith("+"):
        return to_phone
    if to_phone.startswith("0"):
        return "+254" + to_phone[1:]
    if to_phone.startswith("254"):
        return "+" + to_phone
    return to_phone


def _post_request(url: str, payload: dict):
    """Unified POST request handler for Infobip APIs with error handling and logging."""
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        try:
            data = response.json()
        except ValueError:
            data = {"error": "Invalid JSON response", "raw": response.text}

        logger.info("Infobip [%s] Response: %s", response.status_code, data)

    except Exception as e:
        logger.error("Infobip request failed: %s", str(e))
        return False, {"error": str(e)}

    if response.status_code in [200, 201]:
        return True, data
    return False, data


# ---------------- SMS ---------------- #
def send_sms_via_infobip(to_phone: str, message_text: str, parameters: dict = None):
    """Send SMS via Infobip with optional template placeholders."""
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

    success, data = _post_request(url, payload)
    return success, data


# ---------------- WhatsApp Text ---------------- #
def send_whatsapp_via_infobip(to_phone: str, message_text: str, parameters: dict = None):
    """Send plain text WhatsApp message via Infobip."""
    message_text = _replace_placeholders(message_text, parameters)
    to_phone = _format_phone(to_phone)

    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/text"
    payload = {
        "from": INFOBIP_SENDER_WHATSAPP,
        "to": to_phone,
        "content": {"type": "text", "text": message_text},
    }

    success, data = _post_request(url, payload)
    return success, data


# ---------------- WhatsApp Media ---------------- #
def send_whatsapp_media_via_infobip(to_phone: str, media_url: str, caption: str = ""):
    """
    Send WhatsApp media (image, video, document, audio) via Infobip.
    - media_url must be publicly accessible.
    - caption is optional and trimmed for safety.
    """
    caption = (caption or "").strip()
    if len(caption) > 1024:  # WhatsApp caption length limit
        caption = caption[:1021] + "..."

    to_phone = _format_phone(to_phone)

    # Guess type from file extension
    mime_type, _ = mimetypes.guess_type(media_url)
    media_type = "image"
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

    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/media"
    payload = {
        "from": INFOBIP_SENDER_WHATSAPP,
        "to": to_phone,
        "content": {"type": media_type, "mediaUrl": media_url, "caption": caption},
    }

    success, data = _post_request(url, payload)
    return success, data


# ---------------- Contacts Sync ---------------- #
def sync_contact_to_infobip(name: str, phone_number: str):
    """Register or update a contact in Infobip People."""
    phone_number = _format_phone(phone_number)
    url = f"{INFOBIP_BASE_URL}/people/2/persons"
    payload = {"firstName": name, "phoneNumbers": [phone_number]}

    return _post_request(url, payload)
