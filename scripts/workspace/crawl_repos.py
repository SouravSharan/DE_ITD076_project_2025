import requests
import subprocess
import os
import time

# Read the token from a file
def get_github_token():
    token_file = "/workspace/github_token.txt"  # Path to token file
    try:
        with open(token_file, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        raise ValueError("❌ ERROR: GitHub token file not found!")

# Set the token
GITHUB_TOKEN = get_github_token()

if not GITHUB_TOKEN:
    raise ValueError("❌ ERROR: GitHub token missing! Set it using: export GITHUB_TOKEN='your_personal_access_token_here'")

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} 
SEARCH_URL = "https://api.github.com/search/code"
REPO_URL = "https://api.github.com/repos/{}"
QUERY = "filename:pom.xml"
PER_PAGE = 50  
MAX_PAGES = 5  
MAX_REPOS_TO_DOWNLOAD = 10  # Set the limit for repositories to be cloned

def search_repos():
    repos = set()
    print("🔍 Starting GitHub repo search...")
    
    for page in range(1, MAX_PAGES + 1):
        print(f"📄 Searching page {page}/{MAX_PAGES}...")
        params = {"q": QUERY, "per_page": PER_PAGE, "page": page}
        resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)
        
        if resp.status_code == 401:
            raise ValueError("❌ ERROR: Unauthorized (Check your GitHub token)")
        elif resp.status_code != 200:
            raise ValueError(f"❌ ERROR: GitHub API request failed with status {resp.status_code}")

        data = resp.json()
        found_count = len(data.get("items", []))
        print(f"✅ Found {found_count} repositories on page {page}.")
        
        for item in data.get("items", []):
            if len(repos) >= MAX_REPOS_TO_DOWNLOAD:
                print("⚠️ Reached maximum repository limit. Stopping search.")
                return list(repos)

            repo = item["repository"]
            repo_resp = requests.get(REPO_URL.format(repo["full_name"]), headers=HEADERS)
            if repo_resp.status_code == 200:
                repo_data = repo_resp.json()
                repos.add((repo["full_name"], repo_data["clone_url"]))
            else:
                print(f"⚠️ Warning: Failed to fetch details for {repo['full_name']}")
            time.sleep(0.5)  
        
        time.sleep(2)
    
    print(f"🔹 Total repositories found: {len(repos)}")
    return list(repos)

def clone_repo(clone_url, dest_dir):
    if not os.path.exists(dest_dir):
        print(f"🚀 Cloning {clone_url}...")
        subprocess.run(["git", "clone", clone_url, dest_dir], check=True)
    else:
        print(f"⚠️ Skipping {dest_dir}, already exists.")

def main():
    os.makedirs("/workspace/cloned_repos", exist_ok=True)
    repos = search_repos()
    print(f"📁 Found {len(repos)} repositories with pom.xml.")

    for idx, (full_name, clone_url) in enumerate(repos, start=1):
        if idx > MAX_REPOS_TO_DOWNLOAD:
            print("⚠️ Reached maximum repository download limit.")
            break

        name = full_name.replace("/", "_")
        print(f"[{idx}/{MAX_REPOS_TO_DOWNLOAD}] Processing {full_name}...")
        clone_repo(clone_url, f"/workspace/cloned_repos/{name}")

    print("✅ Crawling completed!")

if __name__ == "__main__":
    main()
