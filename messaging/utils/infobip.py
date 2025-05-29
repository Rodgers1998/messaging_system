import os
import requests
from dotenv import load_dotenv

load_dotenv()

INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_SENDER_SMS = os.getenv("INFOBIP_SENDER_SMS", "SHOFCO")
INFOBIP_SENDER_WHATSAPP = os.getenv("INFOBIP_SENDER_WHATSAPP")

def send_sms_via_infobip(to_phone: str, message_text: str):
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

    if response.status_code == 200:
        data = response.json()
        message_id = data.get("messages", [{}])[0].get("messageId", "")
        return True, message_id
    else:
        return False, response.text


def send_whatsapp_via_infobip(to_phone: str, message_text: str):
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

    if response.status_code == 200:
        data = response.json()
        message_id = data.get("messages", [{}])[0].get("messageId", "")
        return True, message_id
    else:
        return False, response.text
