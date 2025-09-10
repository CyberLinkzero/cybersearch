import requests
from bs4 import BeautifulSoup

SEED_URLS = [
    "https://www.python.org",
    "https://pytorch.org",
    "https://flask.palletsprojects.com"
]

def crawl_external():
    results = []
    for url in SEED_URLS:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent":"CyberSearchBot/1.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string.strip() if soup.title else url
            desc = soup.find("meta", {"name":"description"})
            ogdesc = soup.find("meta", {"property":"og:description"})
            description = (desc["content"] if desc else (ogdesc["content"] if ogdesc else "No description"))

            # 🖼️ Try Open Graph image first
            ogimg = soup.find("meta", {"property":"og:image"})
            if ogimg and ogimg.get("content"):
                image_url = ogimg["content"]
            else:
                # fallback: first <img> tag
                first_img = soup.find("img")
                image_url = first_img["src"] if first_img and first_img.get("src") else ""

            results.append({
                "id": url,
                "title": title,
                "description": description,
                "language": "",
                "stars": "",
                "url": url,
                "page": f"external/{title.replace(' ','_')}.html",
                "image": image_url
            })
        except Exception as e:
            print(f"⚠️ Error crawling {url}: {e}")
    return results
