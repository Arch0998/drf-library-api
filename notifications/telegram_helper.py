import requests

from core.settings.base import (
    load_dotenv,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)


load_dotenv()


def send_telegram_message(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    return response.ok
