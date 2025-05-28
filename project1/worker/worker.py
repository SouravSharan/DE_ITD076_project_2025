import pika
import os
import subprocess
import time
import xml.etree.ElementTree as ET
import shutil

MASTER_IP = 'MAster ip'
RESULTS_DIR = '/home/ubuntu/project1/results'
DOCKER_IMAGE = 'tester'

def parse_surefire_reports(results_dir):
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0

    if not os.path.exists(results_dir):
        print(f"No results directory at {results_dir}")
        return None

    for filename in os.listdir(results_dir):
        if not filename.endswith('.xml'):
            continue
        filepath = os.path.join(results_dir, filename)
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            tests = int(root.attrib.get('tests', 0))
            failures = int(root.attrib.get('failures', 0))
            errors = int(root.attrib.get('errors', 0))
            skipped = int(root.attrib.get('skipped', 0))

            total_tests += tests
            total_failures += failures
            total_errors += errors
            total_skipped += skipped
        except Exception as e:
            print(f"Failed to parse {filepath}: {e}")

    return total_tests, total_failures, total_errors, total_skipped


def callback(ch, method, properties, body):
    repo = body.decode()
    repo_name = repo.rstrip('/').split('/')[-1].replace('.git', '')
    print(f"[START] Running tests for {repo}")

    results_path = os.path.join(RESULTS_DIR, repo_name)

    try:
        if os.path.exists(results_path):
            shutil.rmtree(results_path)

        subprocess.run(
            [
                'docker', 'run', '--rm',
                '-e', f'REPO_URL={repo}',
                '-v', f'{RESULTS_DIR}:/results',
                DOCKER_IMAGE
            ],
            check=True,
            timeout=300
        )

        try:
            test_results = parse_surefire_reports(results_path)
        except Exception as parse_err:
            print(f"[PARSER ERROR] Failed to parse results: {parse_err}")
            test_results = None

        if test_results:
            tests, failures, errors, skipped = test_results
            print(f"Test results for {repo_name}:")
            print(f"  Tests run: {tests}")
            print(f"  Failures: {failures}")
            print(f"  Errors: {errors}")
            print(f"  Skipped: {skipped}")
        else:
            print("No test results found or could not parse results.")

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Docker test run timed out for {repo}")

    except subprocess.CalledProcessError as e:
        print(f"[DOCKER ERROR] {e}")

    except Exception as e:
        print(f"[UNEXPECTED ERROR] {e}")

    finally:
        print(f"[ACK] Removing {repo} from queue")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=MASTER_IP)
            )
            channel = connection.channel()
            channel.queue_declare(queue='repo_tasks')

            # Fair dispatch: one un-acked message at a time
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue='repo_tasks',
                on_message_callback=callback,
                auto_ack=False
            )

            print("Worker is waiting for jobs...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            print(f"Connection error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

        except Exception as e:
            print(f"Unexpected error in main loop: {e}. Restarting in 5 seconds...")
            time.sleep(5)


if __name__ == '__main__':
    main()
