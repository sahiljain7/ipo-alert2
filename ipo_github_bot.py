import json
import requests
from datetime import datetime
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
STATUS_FILE = "ipo_status.json"

NSE_API = "https://www.nseindia.com/api/ipo-current-issue"
HEADERS = {"User-Agent": "Mozilla/5.0"}
MIN_ISSUE_SIZE = 500  # Cr

# Load/save JSON
def load_status():
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

def parse_issue_size(size_str):
    return float(size_str.replace(",", "").strip())

def get_ipos():
    try:
        r = requests.get(NSE_API, headers=HEADERS, timeout=20)
        return r.json()
    except:
        return []

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": text})

def main():
    status = load_status()
    ipos = get_ipos()
    today = datetime.today().strftime("%d-%b-%Y")

    for ipo in ipos:
        try:
            size = parse_issue_size(ipo["issueSize"])
        except:
            continue
        if size < MIN_ISSUE_SIZE:
            continue

        name = ipo["companyName"]
        status.setdefault(name, {"notified_open": False, "notified_last_day": False})

        # Open alert
        if ipo.get("status","").lower() == "open" and not status[name]["notified_open"]:
            msg = f"📢 IPO OPEN\n\nName: {name}\nSize: ₹{size} Cr\nDates: {ipo['issueStartDate']} → {ipo['issueEndDate']}\nInterested? Reply YES/NO."
            send_message(msg)
            status[name]["notified_open"] = True

        # Last day alert
        if ipo.get("issueEndDate","") == today and not status[name]["notified_last_day"]:
            msg = f"⚠️ LAST DAY TO APPLY\n\nName: {name}\nSize: ₹{size} Cr\nDates: {ipo['issueStartDate']} → {ipo['issueEndDate']}\nSubscription info may be available on NSE site."
            send_message(msg)
            status[name]["notified_last_day"] = True

    save_status(status)

if __name__ == "__main__":
    main()
