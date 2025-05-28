#!/bin/bash

echo "🚀 Starting distributed setup using Docker Compose..."

# Step 1: Stop and remove existing containers
docker-compose down --remove-orphans

# Step 2: Start containers (No need to rebuild because workspace/ is mounted dynamically)
docker-compose up -d

echo "📌 Containers started successfully!"

# Step 3: Set timezone automatically for all containers (Prevents manual input prompts)
for node in master-node worker1 worker2 worker3 worker4; do
    echo "🕒 Setting timezone for $node..."
    docker exec -it "$node" bash -c "ln -fs /usr/share/zoneinfo/UTC /etc/localtime && dpkg-reconfigure -f noninteractive tzdata"
done

echo "✅ Timezone configured for all containers!"

# Step 4: Ensure GitHub API token is correctly set inside master node
TOKEN_FILE="/workspace/github_token.txt"

if ! docker exec -it master-node test -f "$TOKEN_FILE"; then
    echo "❌ ERROR: GitHub token file ($TOKEN_FILE) not found in master container!"
    exit 1
fi

echo "🔐 GitHub Token verified!"

# Step 5: Run repository crawling script inside master container
echo "🔍 Crawling repositories..."
docker exec -it master-node python3 /workspace/crawl_repos.py

echo "✅ Repository crawling completed!"

# Step 6: Distribute workload for unit testing
echo "🛠️ Running distributed unit tests..."
docker exec -it master-node python3 /workspace/test_repos.py

echo "✅ Unit tests executed across workers!"

# Step 7: Collect performance metrics
echo "📊 Collecting execution metrics..."
docker exec -it master-node docker stats --no-stream | tee /workspace/test_metrics.log

echo "✅ Performance metrics collected!"

echo "🎉 All tasks successfully completed!"
