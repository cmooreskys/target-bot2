import os, requests, time
from datetime import datetime
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
TARGET_EMAIL = os.getenv("TARGET_EMAIL")
TARGET_PASSWORD = os.getenv("TARGET_PASSWORD")

TARGET_TCINS = {
    "1010892076": "30th Celebration ETB",
    "95093989": "Ascended Heroes Deluxe Pin Collection",
    "95120834": "Ascended Heroes Booster Bundle",
    "95082118": "ME 2.5 ETB",
    "1010892068": "30th Sylveon EX Box",
    "1010892070": "30th Knock Out Collection",
    "1010892069": "30th Greninja EX Box",
    "1011447490": "30th Celebration Booster Bundle Box",
    "1012422107": "30th Celebration Mini Tin",
    "1010892067": "30th Poster Collection",
}

def send_discord(msg):
    if not DISCORD_WEBHOOK: return
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=15)
    except Exception as e:
        print(f"Discord error {e}")

def check_stock():
    headers = {"User-Agent": "Mozilla/5.0"}
    live = []
    for tcin, name in TARGET_TCINS.items():
        try:
            url = f"https://www.target.com/p/-/{tcin}"
            r = requests.get(url, headers=headers, timeout=15)
            txt = r.text.lower()
            if r.status_code in [403, 404, 429, 435]:
                print(f"Target {tcin} [{name}]: OOS / blocked ({r.status_code})")
                continue
            if "add to cart" in txt or "ship it" in txt:
                print(f"Target {tcin} [{name}]: IN STOCK")
                live.append((tcin, name, url))
            else:
                print(f"Target {tcin} [{name}]: OOS")
        except Exception as e:
            print(f"Target {tcin} [{name}]: Error {e}")
        time.sleep(1)
    return live

def try_autobuy(tcin, name, url):
    print(f"Trying auto-buy for {name}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://www.target.com/login", timeout=60000)
            page.fill('input#username', TARGET_EMAIL, timeout=15000)
            page.fill('input#password', TARGET_PASSWORD, timeout=15000)
            page.click('button:has-text("Sign in")')
            page.wait_for_timeout(5000)
            
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)
            
            # Try Add to Cart
            try:
                page.click('button:has-text("Add to cart")', timeout=10000)
                print(f"Added {name} to cart")
                page.wait_for_timeout(3000)
                page.goto("https://www.target.com/cart", timeout=60000)
                page.wait_for_timeout(3000)
                # Try checkout - Target will block CAPTCHA here
                page.click('button:has-text("Checkout")', timeout=10000)
                print(f"Checkout attempted for {name}")
                send_discord(f"@everyone 🛒 AUTO-BUY ATTEMPTED for {name} - CHECK YOUR CART: {url}")
            except Exception as e:
                print(f"Auto-buy blocked (expected CAPTCHA): {e}")
                send_discord(f"@everyone 🚨 **TARGET LIVE** 🚨 {name} is live but auto-buy hit CAPTCHA - BUY MANUALLY NOW: {url}")

            browser.close()
    except Exception as e:
        print(f"Auto-buy error: {e}")

if __name__ == "__main__":
    print("Starting Discord + Auto-buy pinger...")
    if not TARGET_EMAIL or not TARGET_PASSWORD:
        print("WARNING: TARGET_EMAIL/PASSWORD not set - will only ping Discord")
    
    live_items = check_stock()
    if live_items:
        for tcin, name, url in live_items:
            msg = f"@everyone 🚨 **TARGET LIVE** 🚨 {name}\n{url}"
            send_discord(msg)
            if TARGET_EMAIL and TARGET_PASSWORD:
                try_autobuy(tcin, name, url)
        print(f"LIVE FOUND: {live_items}")
    else:
        print(f"All OOS - {datetime.now()}")
