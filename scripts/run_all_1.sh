#!/bin/bash

echo "🚀 Starting distributed setup using Docker Compose..."

# Step 1: Stop and remove existing containers
docker-compose down --remove-orphans

# Step 2: Build the image first
echo "🔨 Building master-worker-image..."
docker build -t master-worker-image .

# Step 3: Start containers
docker-compose up -d
echo "📌 Containers started successfully!"

# Step 3: Wait for k3s to be ready
echo "⏳ Waiting for k3s control plane to be ready..."
while ! docker exec k8s-control-plane kubectl get nodes >/dev/null 2>&1; do
    echo "Waiting for k3s..."
    sleep 5
done

# Step 4: Wait for k3s to be ready
sleep 15

# Step 5: Copy and apply RBAC first
echo "🔐 Setting up RBAC..."
docker cp ./job-role.yaml k8s-control-plane:/tmp/
docker exec k8s-control-plane kubectl apply -f /tmp/job-role.yaml

# Step 6: Copy worker deployment to k3s control plane and apply it
echo "🛠️ Deploying worker pods..."
docker cp ./workspace/worker-deployment.yaml k8s-control-plane:/tmp/
docker exec k8s-control-plane kubectl apply -f /tmp/worker-deployment.yaml

# Step 7: Configure kubeconfig for master-node
echo "🔧 Configuring Kubernetes access..."
docker exec master-node mkdir -p /root/.kube

# Get the k3s server IP from the control plane container
K3S_SERVER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' k8s-control-plane)

# Extract kubeconfig and modify server URL
docker exec k8s-control-plane cat /etc/rancher/k3s/k3s.yaml | \
    sed "s/127.0.0.1:6443/${K3S_SERVER_IP}:6443/g" | \
    sed "s/localhost:6443/${K3S_SERVER_IP}:6443/g" > temp_kubeconfig.yaml

# Copy to master node
docker cp temp_kubeconfig.yaml master-node:/root/.kube/config
rm temp_kubeconfig.yaml

# Set proper permissions
docker exec master-node chmod 600 /root/.kube/config

# Step 8: Verify cluster access from master-node
echo "🔍 Verifying Kubernetes access from master-node..."
sleep 5

# Test connection
if docker exec master-node kubectl get nodes; then
    echo "✅ Kubernetes access configured successfully!"
    docker exec master-node kubectl get pods -A
else
    echo "❌ Kubernetes access failed. Trying alternative approach..."
    
    # Alternative: Use service account token
    echo "🔑 Setting up service account authentication..."
    docker exec k8s-control-plane kubectl create serviceaccount automation-sa --dry-run=client -o yaml | docker exec -i k8s-control-plane kubectl apply -f -
    docker exec k8s-control-plane kubectl create clusterrolebinding automation-sa-binding --clusterrole=cluster-admin --serviceaccount=default:automation-sa --dry-run=client -o yaml | docker exec -i k8s-control-plane kubectl apply -f -
    
    # Get token and create kubeconfig
    TOKEN=$(docker exec k8s-control-plane kubectl create token automation-sa)
    cat > temp_sa_kubeconfig.yaml << EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://${K3S_SERVER_IP}:6443
    insecure-skip-tls-verify: true
  name: k3s
contexts:
- context:
    cluster: k3s
    user: automation-sa
  name: k3s
current-context: k3s
users:
- name: automation-sa
  user:
    token: ${TOKEN}
EOF
    
    docker cp temp_sa_kubeconfig.yaml master-node:/root/.kube/config
    rm temp_sa_kubeconfig.yaml
    docker exec master-node chmod 600 /root/.kube/config
    
    # Test again
    docker exec master-node kubectl get nodes
fi

# Step 9: Set timezone for master node
echo "🕒 Setting timezone for master-node..."
docker exec master-node bash -c "ln -fs /usr/share/zoneinfo/UTC /etc/localtime && dpkg-reconfigure -f noninteractive tzdata" 2>/dev/null

# Step 10: Wait for worker pods to be ready (should work now)
echo "⏳ Waiting for worker pods to be ready..."
sleep 30  # Give pods time to start
docker exec master-node kubectl get pods

# Step 11: Run the test workflow
echo "🔍 Running test workflow..."
docker exec -it master-node python /workspace/crawl_repos.py
docker exec -it master-node python /workspace/test_repos.py

echo "🎉 Setup completed successfully!"