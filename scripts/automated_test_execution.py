import os
import subprocess
import json

# Define paths
PROJECTS_DIR = "cloned_repos"
RESULTS_FILE = "test_results.json"

def load_existing_results():
    """Load previous results if file exists"""
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def append_test_results(new_result):
    """Append new test results to JSON file"""
    results = load_existing_results()
    results.append(new_result)

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

def run_maven_tests(repo_path):
    """Runs 'mvn test' and appends results to file"""
    try:
        result = subprocess.run(["mvn", "test"], cwd=repo_path, capture_output=True, text=True)

        output = result.stdout + result.stderr
        total_tests = output.count("Tests run:")
        failed_tests = output.count("Failures:")
        errors = output.count("Errors:")
        skipped = output.count("Skipped:")

        test_result = {
            "repository_name": os.path.basename(repo_path),
            "total_tests": total_tests,
            "failed": failed_tests,
            "errors": errors,
            "skipped": skipped,
            "success": result.returncode == 0
        }

        append_test_results(test_result)
        print(f"✅ Saved results for {test_result['repository_name']}")

    except Exception as e:
        print(f"❌ Error in {repo_path}: {e}")
        append_test_results({"repository_name": os.path.basename(repo_path), "error": str(e)})

def process_repositories(directory):
    """Runs tests across all cloned repositories"""
    for repo in os.listdir(directory):
        repo_path = os.path.join(directory, repo)
        pom_file = os.path.join(repo_path, "pom.xml")

        if os.path.exists(pom_file):
            print(f"🚀 Running tests in {repo}...")
            run_maven_tests(repo_path)

# Start test execution
process_repositories(PROJECTS_DIR)

print(f"✅ All test results are stored in {RESULTS_FILE}")
