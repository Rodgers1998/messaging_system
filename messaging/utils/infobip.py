import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")  # e.g. https://xxxx.api.infobip.com
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_SENDER_SMS = os.getenv("INFOBIP_SENDER_SMS", "SHOFCO")
INFOBIP_SENDER_WHATSAPP = os.getenv("INFOBIP_SENDER_WHATSAPP")


def send_sms_via_infobip(to_phone: str, message_text: str):
    """
    Send SMS message via Infobip
    """
    url = f"{INFOBIP_BASE_URL}/sms/2/text/advanced"
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "messages": [
            {
                "from": INFOBIP_SENDER_SMS,
                "destinations": [{"to": to_phone}],
                "text": message_text,
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        data = response.json()
    except Exception:
        return False, response.text

    if response.status_code == 200:
        message_id = data.get("messages", [{}])[0].get("messageId", "")
        return True, message_id
    else:
        return False, data


def send_whatsapp_via_infobip(to_phone: str, message_text: str):
    """
    Send plain text WhatsApp message via Infobip
    """
    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/text"
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "from": INFOBIP_SENDER_WHATSAPP,
        "to": to_phone,
        "content": {
            "text": message_text
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        data = response.json()
    except Exception:
        return False, response.text

    if response.status_code == 200:
        message_id = data.get("messageId", "")
        return True, message_id
    else:
        return False, data


def sync_contact_to_infobip(name: str, phone_number: str):
    """
    Register or update a contact in Infobip People
    """
    url = f"{INFOBIP_BASE_URL}/people/2/persons"
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "phoneNumbers": [phone_number],
        "firstName": name,
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        data = response.json()
    except Exception:
        return response.status_code, response.text

    if response.status_code in [200, 201]:
        return response.status_code, data
    else:
        return response.status_code, data
