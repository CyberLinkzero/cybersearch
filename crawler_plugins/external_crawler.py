import requests, os, json, random, itertools
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

OUTPUT_DIR = "output"
REFRESH_AFTER_DAYS = 60  # refresh after 2 months

# -------- Static Proxies --------
PROXIES = [
    # {"http": "http://123.45.67.89:8080", "https": "http://123.45.67.89:8080"},
    # {"http": "socks5://127.0.0.1:9050", "https": "socks5://127.0.0.1:9050"},
]
proxy_cycle = itertools.cycle(PROXIES) if PROXIES else None

# -------- Free Proxy Loader --------
def load_free_proxies():
    urls = [
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://www.proxy-list.download/api/v1/get?type=https"
    ]
    proxies = []
    for u in urls:
        try:
            r = requests.get(u, timeout=10)
            if r.ok:
                for line in r.text.strip().splitlines():
                    line = line.strip()
                    if ":" in line:
                        proxies.append({
                            "http": f"http://{line}",
                            "https": f"http://{line}"
                        })
        except Exception:
            continue
    random.shuffle(proxies)
    return proxies

free_proxies = load_free_proxies()
free_proxy_cycle = itertools.cycle(free_proxies) if free_proxies else None

def get_proxy():
    if proxy_cycle:
        return next(proxy_cycle)
    if free_proxy_cycle:
        return next(free_proxy_cycle)
    return None

# -------- Existing Loader --------
def load_existing(prefix="external"):
    existing = {}
    if not os.path.exists(OUTPUT_DIR):
        return existing
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith(prefix) and fname.endswith(".json"):
            try:
                with open(os.path.join(OUTPUT_DIR, fname), "r", encoding="utf-8") as f:
                    for entry in json.load(f):
                        existing[entry["id"]] = entry
            except Exception:
                pass
    return existing

# -------- Seed URLs --------
SEED_URLS = [
    "https://www.python.org",
    "https://pytorch.org",
    "https://flask.palletsprojects.com",
    "https://www.djangoproject.com"
]

# -------- Main Crawler --------
def crawl_external():
    results = []
    existing = load_existing()
    now = datetime.now(timezone.utc)
    refresh_cutoff = now - timedelta(days=REFRESH_AFTER_DAYS)

    for url in SEED_URLS:
        proxy = get_proxy()
        try:
            r = requests.get(url, timeout=15, proxies=proxy, headers={"User-Agent":"CyberSearchBot/1.0"})
            if not r.ok:
                print(f"❌ Failed {url}: {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string.strip() if soup.title else url

            desc = soup.find("meta", {"name":"description"})
            ogdesc = soup.find("meta", {"property":"og:description"})
            description = (desc["content"] if desc else (ogdesc["content"] if ogdesc else "No description"))

            # 🖼️ Get image
            ogimg = soup.find("meta", {"property":"og:image"})
            if ogimg and ogimg.get("content"):
                image_url = ogimg["content"]
                if image_url.startswith("/"):
                    image_url = url.rstrip("/") + image_url
            else:
                first_img = soup.find("img")
                if first_img and first_img.get("src"):
                    image_url = first_img["src"]
                    if image_url.startswith("/"):
                        image_url = url.rstrip("/") + image_url
                else:
                    image_url = ""

            prev = existing.get(url)
            if prev:
                try:
                    crawled_at = datetime.fromisoformat(prev.get("crawled_at"))
                except Exception:
                    crawled_at = datetime.min.replace(tzinfo=timezone.utc)
                if crawled_at >= refresh_cutoff:
                    print(f"⏩ Skipped (fresh) {url}")
                    continue
                else:
                    print(f"♻️ Refreshed {url}")
            else:
                print(f"🆕 New {url}")

            results.append({
                "id": url,
                "title": title,
                "description": description,
                "language": "",
                "stars": "",
                "url": url,
                "page": f"external/{title.replace(' ','_')}.html",
                "image": image_url,
                "crawled_at": now.isoformat()
            })
        except Exception as e:
            print(f"⚠️ Error crawling {url}: {e}")
    return results
