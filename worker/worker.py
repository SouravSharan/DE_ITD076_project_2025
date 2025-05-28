import pika
import subprocess
import os
import shutil
import time

RABBITMQ_HOST = "130.238.29.241"  # Ansible client host (RabbitMQ server)
QUEUE_NAME = "repo_queue"
DOCKER_IMAGE = "mvn-test-runner"

PROCESSED_COUNT = 0
CLEANUP_THRESHOLD = 10  # Number of repos after which Docker cleanup runs
processed_repos = []

def docker_cleanup():
    print("🪜 Running Docker cleanup to free up space...")
    subprocess.run(["docker", "system", "prune", "-af"])

def callback(ch, method, properties, body):
    global PROCESSED_COUNT

    repo_url = body.decode()
    print(f"📅 Received repo: {repo_url}")
    repo_name = repo_url.rstrip('/').split('/')[-1]
    processed_repos.append(repo_name)

    try:
        # ✅ 1. Clean previous repo folder on the host
        if os.path.exists(repo_name):
            print(f"🪛 Repo {repo_name} already exists. Removing it.")
            shutil.rmtree(repo_name, ignore_errors=True)

        # ✅ 2. Clone the repository (shallow clone)
        subprocess.run(["git", "clone", "--depth", "1", repo_url], check=True)

        # ✅ 3. Run the unit tests in Docker
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{os.path.abspath(repo_name)}:/app",
            DOCKER_IMAGE,
            "sh", "-c", "cd /app && mvn test"
        ], check=True)

    except Exception as e:
        print(f"❌ Error during processing {repo_name}: {e}")

    finally:
        # ✅ 4. Final cleanup on host (optional)
        if os.path.exists(repo_name):
            print(f"🪛 Final cleanup of {repo_name} on host")
            shutil.rmtree(repo_name, ignore_errors=True)

        # ✅ 5. Acknowledge task completion to RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)

        # ✅ 6. Periodic Docker system cleanup
        PROCESSED_COUNT += 1
        if PROCESSED_COUNT % CLEANUP_THRESHOLD == 0:
            docker_cleanup()

        # ✅ 7. Log the processed repo
        with open("processed_repos.log", "w") as f:
            for repo in processed_repos:
                f.write(repo + "\n")

while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        print("🔁 Waiting for messages. To exit, press CTRL+C")
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        print("⚠️ Lost connection to RabbitMQ. Retrying in 5 seconds...")
        time.sleep(5)
