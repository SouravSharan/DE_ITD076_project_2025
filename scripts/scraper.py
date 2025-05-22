import requests
import subprocess
import os
import time

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set your GitHub token as an environment variable
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
SEARCH_URL = "https://api.github.com/search/code"
REPO_URL = "https://api.github.com/repos/{}"
QUERY = "filename:pom.xml"
PER_PAGE = 50  # Lower to avoid hitting secondary rate limits
MAX_PAGES = 5  # Adjust as needed

def search_repos():
    repos = set()
    for page in range(1, MAX_PAGES + 1):
        params = {
            "q": QUERY,
            "per_page": PER_PAGE,
            "page": page
        }
        resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)
        print(f"Status: {resp.status_code}, URL: {resp.url}")
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            repo = item["repository"]
            # Fetch repo details to get clone_url
            repo_resp = requests.get(REPO_URL.format(repo["full_name"]), headers=HEADERS)
            if repo_resp.status_code == 200:
                repo_data = repo_resp.json()
                repos.add((repo["full_name"], repo_data["clone_url"]))
            else:
                print(f"Failed to fetch repo details for {repo['full_name']}")
            time.sleep(0.5)  # Be nice to the API
        # Respect rate limits
        time.sleep(2)
    return list(repos)

def is_java_repo(full_name):
    url = REPO_URL.format(full_name)
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"Failed to fetch repo info for {full_name}")
        return False
    data = resp.json()
    language = data.get("language")
    if language is None:
        print(f"Repo {full_name} has no detected language.")
        return False
    return language.lower() == "java"

def clone_repo(clone_url, dest_dir):
    if not os.path.exists(dest_dir):
        subprocess.run(["git", "clone", clone_url, dest_dir], check=True)
    else:
        print(f"Directory {dest_dir} already exists, skipping.")

def main():
    repos = search_repos()
    print(f"Found {len(repos)} repositories with pom.xml.")
    java_repos = []
    for full_name, clone_url in repos:
        print(f"Checking if {full_name} is a Java repo...")
        if is_java_repo(full_name):
            java_repos.append((full_name, clone_url))
        else:
            print(f"Skipping {full_name}, not a Java repo.")
        time.sleep(1)  # Be nice to the API

    print(f"Found {len(java_repos)} Java Maven repositories.")
    for full_name, clone_url in java_repos:
        name = full_name.replace("/", "_")
        print(f"Cloning {full_name}...")
        try:
            clone_repo(clone_url, f"./cloned_repos/{name}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {full_name}: {e}")

if __name__ == "__main__":
    os.makedirs("./cloned_repos", exist_ok=True)
    main()