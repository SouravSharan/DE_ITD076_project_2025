#!/bin/bash

echo "🚀 Starting distributed setup using Docker Compose..."

# Step 1: Stop and remove existing containers
docker-compose down --remove-orphans

# Step 2: Start containers
docker-compose up -d
echo "📌 Containers started successfully!"

# Step 3: Wait for k3s to be ready
echo "⏳ Waiting for k3s control plane to be ready..."
while ! docker exec k8s-control-plane kubectl get nodes >/dev/null 2>&1; do
    sleep 5
done

# Step 4: Copy worker deployment to k3s control plane and apply it
echo "🛠️ Deploying worker pods..."
docker cp ./workspace/worker-deployment.yaml k8s-control-plane:/tmp/
docker exec k8s-control-plane kubectl apply -f /tmp/worker-deployment.yaml

# Step 5: Configure kubeconfig properly
echo "🔧 Configuring Kubernetes access..."
# Create .kube directory if it doesn't exist
docker exec master-node mkdir -p /root/.kube
# Get kubeconfig and modify it
docker exec k8s-control-plane sh -c "cat /etc/rancher/k3s/k3s.yaml | sed 's/server: .*/server: https:\/\/k8s-control-plane:6443/g'" > k3s.yaml
docker cp k3s.yaml master-node:/root/.kube/config
rm k3s.yaml

# Step 6: Verify cluster access
echo "🔍 Verifying Kubernetes access..."
# Wait for cluster to be ready
sleep 10
docker exec master-node kubectl get nodes
docker exec master-node kubectl get pods -A

# Step 7: Set timezone for master node
echo "🕒 Setting timezone for master-node..."
docker exec master-node bash -c "ln -fs /usr/share/zoneinfo/UTC /etc/localtime && dpkg-reconfigure -f noninteractive tzdata"

# Step 8: Run the test workflow
echo "🔍 Running test workflow..."
docker exec -it master-node python /workspace/crawl_repos.py
docker exec -it master-node python /workspace/test_repos.py

echo "🎉 Setup completed successfully!"