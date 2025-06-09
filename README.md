# DE_ITD076_project_2025
Data engineering II ITD076 Project, 2025, Group 16

**Automated Repository Cloning, Distributed Testing, and Performance Metrics Collection using Docker & Kubernetes**

## 📌 **Use Case**
This project is designed for **automated repository crawling**, **distributed unit testing**, and **performance metric collection** using **Docker and Kubernetes**.

### 🔹 **Core Features**
- 🖥️ **Repository Cloning** → Automatically searches and clones repositories containing `pom.xml`.
- ⚙️ **Distributed Testing** → Unit tests are executed across multiple worker nodes using Docker/Kubernetes.
- 📊 **Performance Metrics** → CPU, Memory, and I/O usage are collected from each container.

---

## ⚙️ **Setup**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/YOUR_USERNAME/DE_ITD076_project_2025.git
cd DE_ITD076_project_2025
```
### **2️⃣ Configure GitHub API Token**
Ensure the token is stored correctly:
```bash
echo "YOUR_GITHUB_TOKEN" > workspace/github_token.txt
```
### **3️⃣ Build and Start the Environment**
```bash
docker-compose down --remove-orphans
docker build -t master-worker-image .
docker-compose up -d
```
### **4️⃣ Verify Kubernetes is Running**
```bash
docker exec -it k8s-control-plane kubectl get nodes
```

---

## 🚀 **Running the Project**
### **1️⃣ Start Automated Repository Crawling**
```bash
docker exec -it master-node python3 /workspace/crawl_repos.py
```
### **2️⃣ Run Distributed Unit Tests**
```bash
docker exec -it master-node python3 /workspace/test_repos.py
```
### **3️⃣ Collect Performance Metrics**
```bash
docker exec -it master-node docker stats --no-stream | tee /workspace/test_metrics.log
```

---

## 📊 **Results**
After execution, results are stored in the following files:
- ✅ **`cloned_repos/`** → Stores cloned repositories for analysis.
- 📜 **`test_repos.py` logs** → Unit test results across worker nodes.
- 📊 **`test_metrics.log`** → CPU, Memory, and execution stats for each worker.

To view collected performance metrics:
```bash
cat /workspace/test_metrics.log
```
