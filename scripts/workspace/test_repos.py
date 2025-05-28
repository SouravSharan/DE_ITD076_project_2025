from kubernetes import client, config
import os
import time

# Load Kubernetes config
config.load_kube_config()

# Get Kubernetes API client
batch_v1 = client.BatchV1Api()


# Start timer
start_time = time.time()

repo_path = "/workspace/cloned_repos"
repos = [repo for repo in os.listdir(repo_path)]

def create_kubernetes_job(repo_name):
    """Creates a Kubernetes Job for testing the repository"""
    job_name = f"test-{repo_name}".lower().replace("_", "-")

    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": job_name},
        "spec": {
            "template": {
                "metadata": {"labels": {"app": "unit-test"}},
                "spec": {
                    "containers": [
                        {
                            "name": "test-container",
                            "image": "master-worker-image",
                            "command": ["bash", "-c", f"cd /workspace/cloned_repos/{repo_name} && mvn clean test"]
                        }
                    ],
                    "restartPolicy": "Never"
                }
            }
        }
    }

    batch_v1.create_namespaced_job(namespace="default", body=job_manifest)
    print(f"✅ Created Kubernetes job for {repo_name}")

for repo in repos:
    create_kubernetes_job(repo)


# End timer
end_time = time.time()
total_time = end_time - start_time


# Log build time
with open("/workspace/build_time.log", "w") as log_file:
    log_file.write(f"Total build time: {total_time:.2f} seconds\n")

print(f"⏳ Total build time: {total_time:.2f} seconds")
