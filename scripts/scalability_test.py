#!/bin/bash

# Scalability test script
echo "🚀 Starting scalability tests..."

# Test configurations: workers, cpu, memory
CONFIGS=(
    "2 0.5 512m"
    "4 1.0 1Gi"
    "6 1.5 1.5Gi"
    "8 2.0 2Gi"
)

# Function to update worker deployment
update_worker_deployment() {
    local replicas=$1
    local cpu=$2
    local memory=$3
    
    cat > /tmp/worker-deployment-scaled.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-nodes
spec:
  replicas: $replicas
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker-container
        image: master-worker-image
        args: ["sleep", "infinity"]
        resources:
          requests:
            cpu: "${cpu}"
            memory: "${memory}"
          limits:
            cpu: "${cpu}"
            memory: "${memory}"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
      volumes:
      - name: workspace
        hostPath:
          path: /workspace
          type: Directory
EOF
}

# Function to run test with specific configuration
run_test() {
    local config_name=$1
    local replicas=$2
    local cpu=$3
    local memory=$4
    
    echo "🔄 Testing configuration: $config_name (Workers: $replicas, CPU: $cpu, Memory: $memory)"
    
    # Clean up previous jobs
    docker exec k8s-control-plane kubectl delete jobs --all
    
    # Update worker deployment
    update_worker_deployment $replicas $cpu $memory
    docker cp /tmp/worker-deployment-scaled.yaml k8s-control-plane:/tmp/
    docker exec k8s-control-plane kubectl apply -f /tmp/worker-deployment-scaled.yaml
    
    # Wait for workers to be ready
    echo "⏳ Waiting for $replicas workers to be ready..."
    docker exec k8s-control-plane kubectl wait --for=condition=ready pod -l app=worker --timeout=300s
    
    # Record start time
    START_TIME=$(date +%s)
    
    # Run the test
    echo "🏃 Running test workflow..."
    docker exec master-node python /workspace/test_repos.py
    
    # Wait for all jobs to complete and collect results
    docker exec master-node python /workspace/collect_results.py
    
    # Record end time
    END_TIME=$(date +%s)
    TOTAL_TIME=$((END_TIME - START_TIME))
    
    # Save results with configuration info
    echo "📊 Test completed in ${TOTAL_TIME} seconds"
    
    # Create results directory if it doesn't exist
    mkdir -p /tmp/scalability_results
    
    # Copy results with configuration prefix
    docker cp master-node:/workspace/build_results.json "/tmp/scalability_results/results_${config_name}.json"
    docker cp master-node:/workspace/build_summary.txt "/tmp/scalability_results/summary_${config_name}.txt"
    
    # Add configuration info to summary
    echo "Configuration: $replicas workers, $cpu CPU, $memory memory, Total time: ${TOTAL_TIME}s" >> "/tmp/scalability_results/summary_${config_name}.txt"
    
    echo "✅ Results saved for configuration: $config_name"
    echo ""
}

# Run tests for each configuration
for i in "${!CONFIGS[@]}"; do
    config="${CONFIGS[$i]}"
    read -r replicas cpu memory <<< "$config"
    config_name="config_$((i+1))_${replicas}w_${cpu}cpu_${memory}mem"
    
    run_test "$config_name" "$replicas" "$cpu" "$memory"
done

# Generate final comparison report
echo "📊 Generating scalability comparison report..."
cat > /tmp/scalability_results/comparison_report.txt << EOF
=== SCALABILITY TEST COMPARISON REPORT ===
Generated: $(date)

Configuration Summary:
EOF

for i in "${!CONFIGS[@]}"; do
    config="${CONFIGS[$i]}"
    read -r replicas cpu memory <<< "$config"
    config_name="config_$((i+1))_${replicas}w_${cpu}cpu_${memory}mem"
    
    if [ -f "/tmp/scalability_results/summary_${config_name}.txt" ]; then
        echo "Config $((i+1)): $replicas workers, $cpu CPU, $memory memory" >> /tmp/scalability_results/comparison_report.txt
        grep -E "(Maven Builds:|Total Time:|Configuration:)" "/tmp/scalability_results/summary_${config_name}.txt" >> /tmp/scalability_results/comparison_report.txt
        echo "" >> /tmp/scalability_results/comparison_report.txt
    fi
done

echo "🎉 Scalability tests completed!"
echo "📁 Results saved in: /tmp/scalability_results/"
echo "📊 Comparison report: /tmp/scalability_results/comparison_report.txt"

# Copy results back to your host
echo "📋 Copying results to host..."
cp -r /tmp/scalability_results ./scalability_results/
echo "✅ Results available in: ./scalability_results/"
