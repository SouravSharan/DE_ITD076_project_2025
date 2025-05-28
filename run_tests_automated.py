import csv
import subprocess
import os

# Paths
REPO_FOLDER = "repos"
CSV_INPUT = "valid_java_maven_repos.csv"
CSV_OUTPUT = "test_results.csv"

# Helper function to run the Docker test
def run_test(repo_name):
    repo_path = os.path.join(REPO_FOLDER, repo_name)
    if not os.path.exists(repo_path):
        return "NOT_FOUND"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "-v", f"{os.path.abspath(repo_path)}:/app", "mvn-test-runner"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # 5 minutes timeout
        )
        if result.returncode == 0:
            return "PASS"
        else:
            return "FAIL"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return "ERROR"

# Main loop
with open(CSV_INPUT, "r") as infile, open(CSV_OUTPUT, "w", newline="") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    writer.writerow(["repo_name", "status"])

    next(reader)  # Skip header
    for row in reader:
        repo_name = row[0]
        print(f"🧪 Testing {repo_name}...")
        status = run_test(repo_name)
        writer.writerow([repo_name, status])
        print(f"✅ {repo_name}: {status}")
