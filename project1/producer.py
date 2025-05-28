import pika
import time
import csv

def send_tasks_from_csv(filename="crawler/valid_java_maven_repos.csv", limit=50):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='repo_tasks')

    count = 0
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if count >= limit:
                break

            repo_url = row.get("clone_url", "").strip()
            if repo_url:
                channel.basic_publish(exchange='', routing_key='repo_tasks', body=repo_url)
                print(f"📤 Sent task: {repo_url}")
                count += 1
                time.sleep(0.1)

    connection.close()
    print(f"Sent {count} tasks from CSV to queue!")

if __name__ == "__main__":
    send_tasks_from_csv()
