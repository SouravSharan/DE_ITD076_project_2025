import requests
import json
import os
import time

# Replace with your GitHub token if needed
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def github_search(query, per_page=100, page=1):
    headers = {}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    params = {'q': query, 'per_page': per_page, 'page': page}
    response = requests.get('https://api.github.com/search/repositories', headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()

def crawl_java_maven_projects(num_projects=1000):
    all_projects = []
    query = 'language:Java filename:pom.xml'
    per_page = 100
    page = 1

    while len(all_projects) < num_projects:
        try:
            results = github_search(query, per_page, page)
            if not results['items']:
                print("No more projects found.")
                break

            for item in results['items']:
                all_projects.append({
                    'url': item['html_url'],
                    'owner': item['owner']['login'],
                    'repo_name': item['name'],
                    'clone_url': item['clone_url']
                    # Add other relevant information you need
                })

            print(f"Fetched {len(all_projects)} projects...")
            page += 1
            time.sleep(1) # Be mindful of rate limits

        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")
            time.sleep(10) # Wait longer if there's an error
        except ValueError as e:
            print(f"Error decoding JSON: {e}")
            break

        if page > 10: # Basic safeguard against infinite loops
            print("Reached maximum number of pages to check (for demonstration).")
            break

    return all_projects[:num_projects] # Ensure we don't exceed the target

if __name__ == "__main__":
    java_maven_projects = crawl_java_maven_projects()
    print(f"Found {len(java_maven_projects)} Java projects with Maven.")
    # Save the list to a file (e.g., projects.json)
    with open("java_maven_projects.json", "w") as f:
        json.dump(java_maven_projects, f, indent=4)