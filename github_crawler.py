import requests
import csv
import time

GITHUB_TOKEN = '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'  # Replace this with your GitHub token
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}
BASE_URL = 'https://api.github.com/search/repositories'
CSV_FILE = 'java_maven_repos.csv'

# Create CSV file to store results
with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['name', 'full_name', 'html_url', 'clone_url', 'stars'])

    for page in range(1, 11):  # 10 pages × 100 results = 1000
        print(f"📄 Fetching page {page}...")
        params = {
            "q": "language:Java stars:>20",
            "sort": "stars",
            "order": "desc",
            "per_page": 100,
            "page": page
        }

        response = requests.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 200:
            items = response.json()['items']
            for repo in items:
                writer.writerow([
                    repo['name'],
                    repo['full_name'],
                    repo['html_url'],
                    repo['clone_url'],
                    repo['stargazers_count']
                ])
        else:
            print(f"❌ Failed on page {page}: {response.status_code}")
            print(response.text)
            break

        time.sleep(2)  # Be polite to GitHub API

print(f"✅ Done! Saved results to {CSV_FILE}")

