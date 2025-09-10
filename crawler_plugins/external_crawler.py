import requests
from bs4 import BeautifulSoup

SEED_URLS = ["https://www.python.org", "https://pytorch.org"]

def crawl_external():
    results = []
    for url in SEED_URLS:
        try:
            r = requests.get(url, timeout=5)
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string if soup.title else url
            desc = soup.find("meta", {"name":"description"})
            description = desc["content"] if desc else "No description"
            results.append({
                "id": url,
                "title": title,
                "description": description,
                "language": "",
                "stars": "",
                "url": url,
                "page": f"external/{title.replace(' ','_')}.html"
            })
        except Exception as e:
            print(f"⚠️ Error crawling {url}: {e}")
    return results
