import requests
import csv
import time

# === CONFIGURATION ===
GITHUB_TOKEN = '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'  # Replace with your token
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}
BASE_URL = 'https://api.github.com/search/repositories'
OUTPUT_FILE = 'java_maven_50.csv'

# === SETUP CSV FILE ===
with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['name', 'full_name', 'html_url', 'clone_url', 'stargazers_count'])

    # === Only need 50 results, 1 page of 50 ===
    params = {
    'q': 'language:Java topic:maven stars:>100',
    'sort': 'stars',
    'order': 'desc',
    'per_page': 50,
    'page': 1
}
    print("🔍 Sending request to GitHub API...")
    print(f"🔗 Query URL: {BASE_URL}?q={params['q']}")
    response = requests.get(BASE_URL, headers=HEADERS, params=params)

    if response.status_code == 200:
        repos = response.json()['items']
        print(f"✅ Retrieved {len(repos)} repositories")

        for repo in repos:
            writer.writerow([
                repo['name'],
                repo['full_name'],
                repo['html_url'],
                repo['clone_url'],
                repo['stargazers_count']
            ])
        print(f"📁 Saved to {OUTPUT_FILE}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.json())
