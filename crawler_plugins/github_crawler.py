import requests, time

def crawl_github():
    terms = ["ai", "python", "security", "web", "ml"]
    projects = []
    for term in terms:
        url = f"https://api.github.com/search/repositories?q={term}&sort=stars&order=desc&per_page=20"
        r = requests.get(url, headers={"Accept":"application/vnd.github+json"})
        if r.status_code == 200:
            for repo in r.json().get("items", []):
                projects.append({
                    "id": str(repo["id"]),
                    "title": repo["name"],
                    "description": repo["description"] or "",
                    "language": repo["language"] or "Unknown",
                    "stars": repo["stargazers_count"],
                    "url": repo["html_url"],
                    "page": f"project/{repo['name']}.html"
                })
        time.sleep(1)
    return projects
