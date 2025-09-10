
import os, json, time
from datetime import datetime
from crawler_plugins.github_crawler import crawl_github
from crawler_plugins.external_crawler import crawl_external

OUTPUT_DIR = "output"
TEMPLATE_DIR = "templates"
CHUNK_SIZE = 50000

def load_template(name):
    with open(os.path.join(TEMPLATE_DIR, name), "r", encoding="utf-8") as f:
        return f.read()

def render_template(template, context):
    for k,v in context.items():
        template = template.replace("{{"+k+"}}", str(v))
    return template

def ensure_dirs():
    os.makedirs(os.path.join(OUTPUT_DIR, "project"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "external"), exist_ok=True)

def save_page(filename, title, description, content):
    base = load_template("base.html")
    html = render_template(base, {
        "title": title,
        "description": description,
        "content": content
    })
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

def chunked_save(data, prefix):
    chunks = [data[i:i+CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
    for i, chunk in enumerate(chunks, start=1):
        with open(os.path.join(OUTPUT_DIR, f"{prefix}{i}.json"), "w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=2)

def generate_homepage():
    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CyberSearch – GitHub & Web Search</title>
<meta name="description" content="CyberSearch: a search engine for GitHub projects and external sites.">
<style>
body {font-family: system-ui, sans-serif; background:#0b0f14; color:#e6edf3; margin:0;}
header {text-align:center; padding:40px;}
input {width:60%; padding:14px; font-size:18px; border-radius:10px; border:none;}
.results {max-width:900px; margin:20px auto;}
.card {background:#161b22; padding:20px; margin:15px 0; border-radius:12px;}
.title {font-size:20px; color:#58a6ff; text-decoration:none;}
</style>
<script src="https://unpkg.com/lunr/lunr.js"></script>
</head>
<body>
<header>
  <h1>⚡ CyberSearch</h1>
  <input type="text" id="searchBox" placeholder="Search projects and sites...">
</header>
<div class="results" id="results"></div>
<script>
async function init() {
  let data = [];
  try { data = data.concat(await fetch("projects1.json").then(r=>r.json())); } catch {}
  try { data = data.concat(await fetch("external1.json").then(r=>r.json())); } catch {}

  const idx = lunr(function () {
    this.ref('id'); this.field('title'); this.field('description'); this.field('language');
    data.forEach(d => this.add(d));
  });

  document.querySelector("#searchBox").addEventListener("input", e => {
    const q = e.target.value;
    const results = idx.search(q);
    document.querySelector("#results").innerHTML = results.map(r=>{
      const doc = data.find(d => d.id === r.ref);
      return `<div class="card">
        <a href="${doc['page']}" class="title">${doc['title']}</a>
        <p>${doc['description']}</p>
        <p>⭐ ${doc.get('stars','')} ${doc.get('language','')}</p>
      </div>`;
    }).join("");
  });
}
init();
</script>
</body></html>"""
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

def generate_sitemap(entries, name):
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for e in entries:
        xml += f"<url><loc>{e['page']}</loc><lastmod>{datetime.utcnow().date()}</lastmod></url>\n"
    xml += "</urlset>"
    with open(os.path.join(OUTPUT_DIR, f"sitemap_{name}.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

def main():
    ensure_dirs()
    print("🔎 Crawling GitHub…")
    projects = crawl_github()
    print("🌐 Crawling external…")
    externals = crawl_external()

    chunked_save(projects, "projects")
    chunked_save(externals, "external")

    # Project pages
    proj_tpl = load_template("project_page.html")
    for p in projects:
        content = render_template(proj_tpl, {
            "repo_url": p["url"],
            "title": p["title"],
            "description": p["description"],
            "stars": p["stars"],
            "language": p["language"],
            "topics": ", ".join(p.get("topics", [])),
            "last_updated": p.get("last_updated", "")
        })
        save_page(os.path.join(OUTPUT_DIR, p["page"]), p["title"], p["description"], content)

    # External pages
    ext_tpl = load_template("external_page.html")
    for e in externals:
        content = render_template(ext_tpl, e)
        save_page(os.path.join(OUTPUT_DIR, e["page"]), e["title"], e["description"], content)

    generate_homepage()
    generate_sitemap(projects, "projects")
    generate_sitemap(externals, "external")

    with open(os.path.join(OUTPUT_DIR, "sitemap_index.xml"), "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>sitemap_projects.xml</loc></sitemap>
  <sitemap><loc>sitemap_external.xml</loc></sitemap>
</sitemapindex>""")

if __name__ == "__main__":
    main()
