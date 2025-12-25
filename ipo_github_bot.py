import json
import requests
from datetime import datetime
import os
import time

# ======================
# CONFIG
# ======================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
STATUS_FILE = "ipo_status.json"

NSE_API = "https://www.nseindia.com/api/ipo-current-issue"
MIN_ISSUE_SIZE = 500  # Cr

# ======================
# UTILITIES
# ======================
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
    """
    Converts issue size like '1,200 Cr' or '1200' to float
    """
    try:
        size_str = size_str.lower().replace("cr", "").replace(",", "").strip()
        return float(size_str)
    except:
        return 0.0

# ======================
# NSE FETCH (IMPORTANT FIX)
# ======================
def get_ipos():
    """
    NSE blocks requests unless cookies are set.
    This method works in GitHub Actions.
    """
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        })

        # First request to set cookies
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(1)

        r = session.get(NSE_API, timeout=20)
        return r.json()
    except Exception as e:
        print("Error fetching IPO data:", e)
        return []

# ======================
# TELEGRAM
# ======================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)

# ======================
# MAIN LOGIC
# ======================
def main():
    status = load_status()
    ipos = get_ipos()

    today = datetime.today().strftime("%d-%b-%Y")

    if not ipos:
        print("No IPO data received")
        return

    for ipo in ipos:
        try:
            name = ipo.get("companyName", "").strip()
            if not name:
                continue

            size = parse_issue_size(ipo.get("issueSize", ""))
            if size < MIN_ISSUE_SIZE:
                continue

            start_date = ipo.get("issueStartDate", "")
            end_date = ipo.get("issueEndDate", "")
            ipo_status = ipo.get("status", "").lower()

            status.setdefault(name, {
                "notified_open": False,
                "notified_last_day": False
            })

            # ======================
            # OPEN ALERT
            # ======================
            if (
                ipo_status == "open"
                and not status[name]["notified_open"]
            ):
                msg = (
                    f"📢 *IPO OPEN*\n\n"
                    f"*Name:* {name}\n"
                    f"*Issue Size:* ₹{size} Cr\n"
                    f"*Dates:* {start_date} → {end_date}\n\n"
                    f"Interested?"
                )

                send_message(msg)
                status[name]["notified_open"] = True

            # ======================
            # LAST DAY ALERT
            # ======================
            if (
                end_date == today
                and status[name]["notified_open"]
                and not status[name]["notified_last_day"]
            ):
                msg = (
                    f"⏰ *LAST DAY TO APPLY*\n\n"
                    f"*Name:* {name}\n"
                    f"*Issue Size:* ₹{size} Cr\n"
                    f"*Closes Today*\n\n"
                    f"Check subscription details on NSE."
                )

                send_message(msg)
                status[name]["notified_last_day"] = True

        except Exception as e:
            print(f"Error processing IPO {ipo}: {e}")

    save_status(status)

# ======================
if __name__ == "__main__":
    main()
