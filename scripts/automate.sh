#!/bin/bash

echo "🚀 Initiating Automated Setup for Distributed Maven Builds!"

# Step 1: Clean up previous runs
echo "🧹 Cleaning up existing containers..."
docker-compose down --remove-orphans

# Step 2: Build the worker image
echo "🔨 Building Docker image..."
docker build -t master-worker-image .

# Step 3: Start the distributed cluster
echo "📢 Starting up containers..."
docker-compose up -d
echo "✅ Containers are running!"

# Step 4: Wait for Kubernetes control plane to initialize
echo "⏳ Waiting for k3s control plane..."
while ! docker exec k8s-control-plane kubectl get nodes >/dev/null 2>&1; do
    echo "🔄 Still waiting for Kubernetes..."
    sleep 5
done
echo "✅ Kubernetes control plane is ready!"

# Step 5: Setup RBAC for job execution
echo "🔐 Applying RBAC configurations..."
docker cp ./job-role.yaml k8s-control-plane:/tmp/
docker exec k8s-control-plane kubectl apply -f /tmp/job-role.yaml

# Step 6: Crawl Maven repositories and clone them
echo "🔍 Searching and cloning Maven repositories..."
docker exec master-node python /workspace/crawl_repos.py

# Step 7: Deploy worker nodes to run tests
echo "🛠️ Deploying worker pods..."
docker cp ./workspace/worker-deployment.yaml k8s-control-plane:/tmp/
docker exec k8s-control-plane kubectl apply -f /tmp/worker-deployment.yaml

# Step 8: Verify worker pod readiness
echo "⏳ Waiting for worker pods to be ready..."
docker exec k8s-control-plane kubectl wait --for=condition=ready pod -l app=worker --timeout=300s

# Step 9: Trigger Maven build and unit tests in distributed setup
echo "🏃 Running Maven builds and tests..."
docker exec master-node python /workspace/test_repos.py

# Step 10: Collect test results
echo "📊 Collecting results..."
docker exec master-node python /workspace/collect_results.py

# Step 11: Run scalability tests with different resource constraints
echo "📈 Running scalability tests..."
docker exec master-node python /workspace/scalability_test.py

echo "🎉 Automation complete! Results stored in /workspace/scalability_results/"

