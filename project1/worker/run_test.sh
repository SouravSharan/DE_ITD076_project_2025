#!/bin/bash
set -e  # Exit on first error

mkdir -p /workspace
cd /workspace

# Clone the repo
if ! git clone "$REPO_URL" project; then
  echo "[ERROR] Failed to clone $REPO_URL"
  exit 1
fi

cd project || exit 1

# Run tests (suppress output, allow failures to not crash script)
if ! mvn clean test -q; then
  echo "[WARNING] Tests failed for $REPO_URL"
fi

# Extract repo name and prepare results directory
REPO_NAME=$(basename "$REPO_URL" .git)
mkdir -p /results/$REPO_NAME

# Copy test results if they exist
if [ -d "target/surefire-reports" ]; then
  cp target/surefire-reports/*.xml /results/$REPO_NAME/ 2>/dev/null || echo "[INFO] No XML reports found"
else
  echo "[INFO] No surefire-reports directory found"
fi

# Cleanup cloned repo to avoid leftover data
cd /
rm -rf /workspace/project
