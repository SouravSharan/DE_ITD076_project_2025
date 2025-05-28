import csv
import pika

# RabbitMQ connection setup
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='repo_queue', durable=True)

# Read filtered repos and send to queue
with open('valid_java_maven_repos.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        repo_url = row['html_url']
        print(f"📤 Publishing: {repo_url}")
        channel.basic_publish(
            exchange='',
            routing_key='repo_queue',
            body=repo_url,
            properties=pika.BasicProperties(delivery_mode=2)  # Make messages persistent
        )

print("✅ All repositories published to RabbitMQ queue.")
connection.close()

