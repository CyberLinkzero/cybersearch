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

def chunked_save(new_data, prefix):
    """Merge new data into existing JSON shards, dedupe, and resave in chunks."""
    existing = {}
    # Load old data
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith(prefix) and fname.endswith(".json"):
            try:
                with open(os.path.join(OUTPUT_DIR, fname), "r", encoding="utf-8") as f:
                    for entry in json.load(f):
                        existing[entry["id"]] = entry
            except Exception:
                pass

    # Merge: new/updated overwrite old
    for e in new_data:
        existing[e["id"]] = e

    combined = list(existing.values())
    chunks = [combined[i:i+CHUNK_SIZE] for i in range(0, len(combined), CHUNK_SIZE)]
    if not chunks:
        chunks = [[]]

    # Write updated chunks
    for i, chunk in enumerate(chunks, start=1):
        with open(os.path.join(OUTPUT_DIR, f"{prefix}{i}.json"), "w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=2)

def save_html(entry, folder):
    """Generate simple HTML page for each entry."""
    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{entry['title']}</title>
<meta name="description" content="{entry['description']}">
</head><body>
<h1>{entry['title']}</h1>
<p>{entry['description']}</p>
<p><strong>Language:</strong> {entry.get('language','')}</p>
<p><strong>Stars:</strong> {entry.get('stars','')}</p>
<p><a href="{entry['url']}">Visit original</a></p>
<p><em>Crawled at {entry.get('crawled_at','')}</em></p>
</body></html>"""
    with open(os.path.join(OUTPUT_DIR, folder, os.path.basename(entry['page'])), "w", encoding="utf-8") as f:
        f.write(html)

def generate_sitemap(data, filename):
    """Generate XML sitemap from entries."""
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for e in data:
        xml += f"<url><loc>{SITE_BASE}/{e['page']}</loc><lastmod>{datetime.now(timezone.utc).date()}</lastmod></url>\n"
    xml += "</urlset>"
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(xml)

def main():
    ensure_dirs()

    # GitHub projects
    print("🔎 Crawling GitHub…")
    projects = crawl_github()
    print(f"✅ {len(projects)} new/updated GitHub projects")

    # External sites
    print("🌐 Crawling external…")
    externals = crawl_external()
    print(f"✅ {len(externals)} new/updated external sites")

    # Save JSON shards
    chunked_save(projects, "projects")
    chunked_save(externals, "external")

    # Write HTML detail pages
    for p in projects:
        save_html(p, "project")
    for e in externals:
        save_html(e, "external")

    # Generate sitemaps
    generate_sitemap(projects, "sitemap_projects.xml")
    generate_sitemap(externals, "sitemap_external.xml")

    # Sitemap index
    sitemap_index = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>{SITE_BASE}/sitemap_projects.xml</loc></sitemap>
  <sitemap><loc>{SITE_BASE}/sitemap_external.xml</loc></sitemap>
</sitemapindex>"""
    with open(os.path.join(OUTPUT_DIR, "sitemap_index.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_index)

    print("🚀 CyberSearch build complete!")

if __name__ == "__main__":
    main()
