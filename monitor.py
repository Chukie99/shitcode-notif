import os, re, json, requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN","").strip()
CHAT_ID = os.environ.get("CHAT_ID","").strip()
CHANNELS = [c.strip() for c in os.environ.get("CHANNELS","bcgame_official").split(",") if c.strip()]
STATE = "last.json"
CODE_RE = re.compile(r"[A-Z0-9]{3,}-[A-Z0-9]{3,}(?:-[A-Z0-9]{2,})*")

def send(text):
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[SKIP SEND] BOT_TOKEN/CHAT_ID kosong. Pesan: {text[:150]}")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}, timeout=20)
    print("SEND", r.status_code, r.text[:300])

def load_seen():
    try:
        return json.loads(open(STATE, encoding="utf-8").read())
    except: return {}

def save_seen(d):
    open(STATE,"w",encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))

seen = load_seen()
new_found = 0
for ch in CHANNELS:
    ch = ch.lstrip("@")
    url = f"https://t.me/s/{ch}"
    print(f"CHECK {ch} -> {url}")
    try:
        html = requests.get(url, timeout=20, headers={"User-Agent":"Mozilla/5.0"}).text
        soup = BeautifulSoup(html, "html.parser")
        msgs = soup.select("div.tgme_widget_message_text")
        print(f"  found {len(msgs)} msgs")
        for el in msgs[:6]:
            txt = el.get_text("\n", strip=True)
            if not txt: continue
            is_code = ("code" in txt.lower() or "shitcode" in txt.lower() or CODE_RE.search(txt) or "redeem" in txt.lower())
            key = f"{ch}:{txt[:120]}"
            if is_code and key not in seen:
                # ambil link pesan jika ada
                link = f"https://t.me/s/{ch}"
                try:
                    # cari parent message link
                    parent = el.find_parent("div", class_="tgme_widget_message")
                    if parent and parent.get("data-post"):
                        link = f"https://t.me/{parent.get('data-post')}"
                except: pass
                msg = f"🔥 KODE BARU @{ch}\n\n{txt[:600]}\n\n{link}\n\nPaste: bc.game -> Bonus -> Redeem Code"
                print(f"  NEW CODE: {txt[:80]}")
                send(msg)
                seen[key]=1
                new_found+=1
            elif is_code:
                print(f"  seen skip: {txt[:60]}")
    except Exception as e:
        print(f"  ERR {ch}: {e}")

# simpan state selalu agar dedup jalan
save_seen(seen)
print(f"DONE new={new_found} total_seen={len(seen)}")
