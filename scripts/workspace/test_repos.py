import subprocess
import os

workers = ["worker1", "worker2", "worker3", "worker4"]
repo_path = "/workspace/cloned_repos"
repos = [repo for repo in os.listdir(repo_path)]

for repo in repos:
    worker = workers[repos.index(repo) % len(workers)]
    print(f"Running unit tests on {worker} for {repo}...")
    subprocess.run(
        f"docker exec -it {worker} bash -c 'cd /workspace/cloned_repos/{repo} && mvn clean test'",
        shell=True
    )
