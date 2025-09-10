import os, json
from datetime import datetime, timezone
from crawler_plugins.github_crawler import crawl_github
from crawler_plugins.external_crawler import crawl_external

OUTPUT_DIR = "output"
CHUNK_SIZE = 100
SITE_BASE = "https://username.github.io/cybersearch"  # 👈 replace with your GitHub Pages URL

def ensure_dirs():
    os.makedirs(os.path.join(OUTPUT_DIR, "project"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "external"), exist_ok=True)

def chunked_save(data, prefix):
    chunks = [data[i:i+CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
    if not chunks:  # ensure at least one file
        chunks = [[]]
    for i, chunk in enumerate(chunks, start=1):
        with open(os.path.join(OUTPUT_DIR, f"{prefix}{i}.json"), "w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=2)

def save_html(entry, folder):
    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{entry['title']}</title>
<meta name="description" content="{entry['description']}">
</head><body>
<h1>{entry['title']}</h1>
<p>{entry['description']}</p>
<p><a href="{entry['url']}">Visit original</a></p>
</body></html>"""
    with open(os.path.join(OUTPUT_DIR, folder, os.path.basename(entry['page'])), "w", encoding="utf-8") as f:
        f.write(html)

def generate_sitemap(data, filename):
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for e in data:
        xml += f"<url><loc>{SITE_BASE}/{e['page']}</loc><lastmod>{datetime.now(timezone.utc).date()}</lastmod></url>\n"
    xml += "</urlset>"
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(xml)

def main():
    ensure_dirs()
    print("🔎 Crawling GitHub…")
    projects = crawl_github()
    print(f"✅ {len(projects)} GitHub projects")

    print("🌐 Crawling external…")
    externals = crawl_external()
    print(f"✅ {len(externals)} external sites")

    chunked_save(projects, "projects")
    chunked_save(externals, "external")

    for p in projects:
        save_html(p, "project")
    for e in externals:
        save_html(e, "external")

    generate_sitemap(projects, "sitemap_projects.xml")
    generate_sitemap(externals, "sitemap_external.xml")

    # sitemap index
    sitemap_index = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>{SITE_BASE}/sitemap_projects.xml</loc></sitemap>
  <sitemap><loc>{SITE_BASE}/sitemap_external.xml</loc></sitemap>
</sitemapindex>"""
    with open(os.path.join(OUTPUT_DIR, "sitemap_index.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_index)

if __name__ == "__main__":
    main()
