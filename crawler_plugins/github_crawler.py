import requests, time

def crawl_github():
    terms = ["ai", "python", "security", "web", "ml"]  # keywords
    projects = []
    headers = {"Accept":"application/vnd.github+json"}
    token = None
    try:
        import os
        token = os.getenv("GITHUB_TOKEN")
    except:
        pass
    if token:
        headers["Authorization"] = f"Bearer {token}"

    for term in terms:
        url = f"https://api.github.com/search/repositories?q={term}&sort=stars&order=desc&per_page=20"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            for repo in r.json().get("items", []):
                projects.append({
                    "id": str(repo["id"]),
                    "title": repo["name"],
                    "description": repo["description"] or "",
                    "language": repo["language"] or "Unknown",
                    "stars": repo["stargazers_count"],
                    "url": repo["html_url"],
                    "page": f"project/{repo['name']}.html",
                    "image": repo["owner"]["avatar_url"]  # 👈 avatar image
                })
        else:
            print("GitHub API error", r.status_code, r.text[:200])
        time.sleep(0.6)
    return projects
