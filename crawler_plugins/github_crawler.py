import requests, os, json, time, itertools, random
from datetime import datetime, timedelta, timezone

OUTPUT_DIR = "output"
STATE_FILE = os.path.join(OUTPUT_DIR, "github_state.json")
REFRESH_AFTER_DAYS = 60

# -------- Tokens --------
TOKENS = [
    os.getenv("GITHUB_TOKEN1"),
    os.getenv("GITHUB_TOKEN2"),
    os.getenv("GITHUB_TOKEN3"),
]
TOKENS = [t for t in TOKENS if t]
token_cycle = itertools.cycle(TOKENS) if TOKENS else None

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

# -------- Helpers --------
def get_headers():
    headers = {"Accept": "application/vnd.github+json"}
    if token_cycle:
        token = next(token_cycle)
        headers["Authorization"] = f"Bearer {token}"
    return headers

def get_proxy():
    if proxy_cycle:
        return next(proxy_cycle)
    if free_proxy_cycle:
        return next(free_proxy_cycle)
    return None

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_id": 0}

def save_state(state):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

# -------- Main Crawl --------
def crawl_all_github(limit=5000):
    """
    Crawl GitHub repos continuously until limit is hit for this run.
    Resumes from last_id stored in github_state.json.
    """
    state = load_state()
    start_id = state.get("last_id", 0)
    now = datetime.now(timezone.utc)
    refresh_cutoff = now - timedelta(days=REFRESH_AFTER_DAYS)

    url = f"https://api.github.com/repositories?since={start_id}&per_page=100"
    crawled, repos = 0, []

    while url and crawled < limit:
        success = False
        for attempt in range(20):  # rotate proxies/tokens aggressively
            headers = get_headers()
            proxy = get_proxy()
            try:
                r = requests.get(url, headers=headers, proxies=proxy, timeout=20)
            except Exception as e:
                print(f"⚠️ Proxy failed: {proxy} → {e}")
                continue

            if r.status_code in (403, 429):  # rate-limited
                print(f"⚠️ Rate limit hit (proxy={proxy}). Switching...")
                time.sleep(2)
                continue

            if r.status_code == 200:
                items = r.json()
                if not items:
                    print("⚠️ No more repos available.")
                    return repos

                for repo in items:
                    rid = str(repo["id"])
                    repos.append({
                        "id": rid,
                        "title": repo["name"],
                        "description": repo.get("description") or "",
                        "language": repo.get("language") or "Unknown",
                        "stars": repo.get("stargazers_count", 0),
                        "url": repo["html_url"],
                        "page": f"project/{repo['name']}.html",
                        "image": repo["owner"]["avatar_url"],
                        "crawled_at": now.isoformat()
                    })
                    state["last_id"] = repo["id"]
                    crawled += 1

                print(f"✅ Crawled {crawled} repos so far (last_id={state['last_id']})")

                # Parse "next" link for pagination
                url = None
                if "Link" in r.headers:
                    parts = r.headers["Link"].split(",")
                    for p in parts:
                        if 'rel="next"' in p:
                            url = p[p.find("<")+1:p.find(">")]
                            break

                save_state(state)
                success = True
                break
            else:
                print(f"❌ Error {r.status_code}: {r.text[:200]}")
                break

        if not success:
            print("❌ All proxies/tokens failed for this page. Stopping.")
            break

        time.sleep(1)

    return repos
