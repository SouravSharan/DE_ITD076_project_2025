import csv
import os
import subprocess
import shutil

INPUT_CSV = "java_maven_repos.csv"
OUTPUT_CSV = "valid_java_maven_repos.csv"
CLONE_DIR = "repos"

# Create clone directory
os.makedirs(CLONE_DIR, exist_ok=True)

# Open output CSV to store valid repos
with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as valid_file:
    writer = csv.writer(valid_file)
    writer.writerow(['name', 'full_name', 'html_url', 'clone_url', 'stars'])

    # Read input CSV
    with open(INPUT_CSV, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            name = row['name']
            full_name = row['full_name']
            clone_url = row['clone_url']
            stars = row['stars']
            html_url = row['html_url']
            local_path = os.path.join(CLONE_DIR, name)

            print(f"\n🔧 Cloning {name}...")
            if os.path.exists(local_path):
                print("📁 Already cloned, skipping.")
                continue

            try:
                subprocess.run(["git", "clone", "--depth=1", clone_url, local_path], check=True)

                # Find pom.xml files
                pom_files = []
                for root, dirs, files in os.walk(local_path):
                    if 'pom.xml' in files:
                        pom_files.append(os.path.join(root, 'pom.xml'))

                # Check if any pom.xml contains 'junit'
                found_junit = False
                for pom in pom_files:
                    with open(pom, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        if 'junit' in content:
                            found_junit = True
                            break

                if found_junit:
                    print(f"✅ {name} contains JUnit in pom.xml.")
                    writer.writerow([name, full_name, html_url, clone_url, stars])
                else:
                    print(f"❌ {name} does not use JUnit.")

            except subprocess.CalledProcessError:
                print(f"❌ Failed to clone {name}, skipping.")
                continue
