import os, requests, time
from datetime import datetime

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

TARGET_TCINS = {
    "1010892076": "30th Celebration ETB",
    "95093989": "Ascended Heroes Deluxe Pin Collection",
    "95120834": "Ascended Heroes Booster Bundle",
    "95082118": "ME 2.5 ETB",
    "1010892068": "30th Sylveon EX Box",
    "1010892070": "30th Knock Out Collection",
    "1010892069": "30th Greninja EX Box",
    "1011407490": "30th Celebration Booster Bundle Box",
    "1012422107": "30th Celebration Mini Tin",
    "1010892067": "30th Poster Collection",
}

def send_discord(msg):
    if not DISCORD_WEBHOOK:
        print("No webhook set"); return
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=15)
    except Exception as e:
        print(f"Discord error {e}")

def check_target():
    headers = {"User-Agent": "Mozilla/5.0"}
    found = []
    for tcin, name in TARGET_TCINS.items():
        try:
            url = f"https://www.target.com/p/-/{tcin}"
            r = requests.get(url, headers=headers, timeout=15)
            txt = r.text.lower()
            if r.status_code in [403, 404, 429, 435]:
                print(f"Target {tcin} [{name}]: OOS / blocked ({r.status_code})")
                continue
            if "out of stock" in txt or "sold out" in txt or "temporarily out of stock" in txt:
                print(f"Target {tcin} [{name}]: OOS")
            elif "add to cart" in txt or "ship it" in txt:
                print(f"Target {tcin} [{name}]: IN STOCK")
                found.append(f"{name} - https://www.target.com/p/-/{tcin}")
            else:
                print(f"Target {tcin} [{name}]: OOS (unknown)")
        except Exception as e:
            print(f"Target {tcin} [{name}]: Error {e}")
        time.sleep(2)
    return found

if __name__ == "__main__":
    print("Starting Discord pinger...")
    while True:
        live = check_target()
        if live:
            msg = "@everyone 🚨 **TARGET LIVE** 🚨\n" + "\n".join(live)
            send_discord(msg)
            time.sleep(300)  # wait 5 min to avoid spam
        print(f"Sleeping 60s... {datetime.now()}")
        time.sleep(60)
