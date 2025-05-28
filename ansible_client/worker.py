import pika
import subprocess
import os
import shutil
import time

RABBITMQ_HOST = "130.238.29.241"  # Ansible client host (RabbitMQ server)
QUEUE_NAME = "repo_queue"
DOCKER_IMAGE = "mvn-test-runner"

PROCESSED_COUNT = 0
CLEANUP_THRESHOLD = 10  # Run Docker cleanup every 10 repos

def docker_cleanup():
    print("🧼 Running Docker cleanup to free up space...")
    subprocess.run(["docker", "system", "prune", "-af"])

def callback(ch, method, properties, body):
    global PROCESSED_COUNT

    repo_url = body.decode()
    print(f"📥 Received repo: {repo_url}")
    repo_name = repo_url.rstrip('/').split('/')[-1]

    # ✅ 1. Clean existing repo if any
    if os.path.exists(repo_name):
        print(f"🧹 Cleaning up existing repo folder: {repo_name}")
        shutil.rmtree(repo_name, ignore_errors=True)

    # ✅ 2. Clone the repository
    subprocess.run(["git", "clone", repo_url])

    # ✅ 3. Run tests in Docker
    test_result = subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{os.path.abspath(repo_name)}:/app",
        DOCKER_IMAGE,
        "sh", "-c", "cd /app && mvn test"
    ], capture_output=True, text=True)

    # ✅ 4. Log test output if failed
    if test_result.returncode != 0:
        with open("test_failures.log", "a") as f:
            f.write(f"❌ Failed: {repo_url}\n")

    # ✅ 5. Cleanup cloned repo
    if os.path.exists(repo_name):
        print(f"🧹 Final cleanup of {repo_name} on host")
        shutil.rmtree(repo_name, ignore_errors=True)

    # ✅ 6. Acknowledge to RabbitMQ
    ch.basic_ack(delivery_tag=method.delivery_tag)

    # ✅ 7. Periodic cleanup
    PROCESSED_COUNT += 1
    if PROCESSED_COUNT % CLEANUP_THRESHOLD == 0:
        docker_cleanup()

# 🧠 Message loop
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

