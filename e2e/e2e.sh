#!/bin/bash

# Check if KUBECONFIG is set
if [ -z "$KUBECONFIG" ]; then
    echo "Error: KUBECONFIG is not set."
    exit 1
fi

# OpenShift cluster user
export KUBE_SSH_USER=core

# Find the KubeSAN StorageClass
SC_NAME=$(oc get sc -o json | jq -r '.items[] | select(.provisioner=="kubesan.gitlab.io") | .metadata.name' | head -n 1)
if [ -z "$SC_NAME" ]; then
    echo "Error: Could not find an existing KubeSAN StorageClass."
    exit 1
fi

# Get the Kubernetes server version
K8S_VERSION=$(oc version -o json | jq -r '.serverVersion.gitVersion')
if [ -z "$K8S_VERSION" ]; then
    echo "Error: Failed to retrieve Kubernetes version."
    exit 1
fi

# Download and extract test binaries if not already present
if [ ! -f e2e.test ] || [ ! -f ginkgo ]; then
    echo "Downloading and extracting e2e.test and ginkgo binaries..."
    curl --location "https://dl.k8s.io/${K8S_VERSION}/kubernetes-test-linux-amd64.tar.gz" | \
        tar --strip-components=3 -zxf - \
            kubernetes/test/bin/e2e.test \
            kubernetes/test/bin/ginkgo
else
    echo "e2e.test and ginkgo binaries are already present."
fi

# Define Ginkgo skip patterns for clarity
SKIP_PATTERNS=(
    'phemeral*'
    'SELinuxMountReadWriteOncePod.*'
    'subpath.*'
    'different volume mode.*'
    'after modifying source data.*'
)

# Convert skip patterns to a single string separated by '|'
SKIP_STRING=$(IFS='|'; echo "${SKIP_PATTERNS[*]}")

# Run Kubernetes e2e test
echo "Starting e2e test..."
./e2e.test \
    -ginkgo.seed=1 \
    -ginkgo.succinct \
    -ginkgo.focus="External.Storage.*kubesan.gitlab.io.*" \
    -ginkgo.skip="$SKIP_STRING" \
    -ginkgo.junit-report="e2e.xml" \
    -dump-logs-on-failure \
    -storage.testdriver="./kubesan-driver.yaml" \
    -provider=local \
    -allowed-not-ready-nodes=-1

# Upload test results to reportportal if e2e.xml exists
if [ -f "e2e.xml" ]; then
    echo "Uploading test results to reportportal..."
    python3 upload_result.py e2e.xml
    if [ $? -eq 0 ]; then
        echo "Test results uploaded successfully."
    else
        echo "Error: Failed to upload test results."
        exit 1
    fi
else
    echo "Warning: Test results file e2e.xml not found. Skipping upload."
fi

# Completion message
echo "e2e test execution completed."
