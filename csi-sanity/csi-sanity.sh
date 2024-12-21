#!/bin/bash

TIMEOUT=300
START_TIME=$(date +%s)

# Find the KubeSAN StorageClass
SC_NAME=$(oc get sc -o json | jq -r '.items[] | select(.provisioner=="kubesan.gitlab.io") | .metadata.name' | head -n 1)
if [ -z "$SC_NAME" ]; then
    echo "Error: Could not find an existing KubeSAN StorageClass."
    exit 1
fi

oc create -f - <<EOF
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: csi-parameters
data:
  parameters: '$(oc get --output jsonpath={.parameters} sc ${SC_NAME})'
---
apiVersion: v1
kind: Pod
metadata:
  name: csi-sanity
spec:
  containers:
    - name: csi-sanity
      image: quay.io/fedora/fedora:latest
      command: [sleep, infinity]
      volumeMounts:
        - name: drivers
          mountPath: /var/lib/kubelet/plugins
        - name: csi-parameters
          mountPath: /etc/csi-parameters
        - name: dev
          mountPath: /dev
      securityContext:
        privileged: true
  volumes:
    - name: drivers
      hostPath:
        path: /var/lib/kubelet/plugins/
        type: DirectoryOrCreate
    - name: csi-parameters
      configMap:
        name: csi-parameters
    - name: dev
      hostPath:
        path: /dev
        type: Directory
EOF

while true; do
  # Get the pod status using the oc command
  pod_status=$(oc get pod csi-sanity -o jsonpath='{.status.phase}')

  if [ $? -ne 0 ]; then
    echo "$(date) [ERROR] Failed to retrieve pod status."
    sleep 1
    continue
  fi

  # Check if the pod is running
  if [ "$pod_status" == "Running" ]; then
    echo "$(date) [INFO] Pod 'csi-sanity' is running."
    break
  fi

  # Check if the timeout has been reached
  current_time=$(date +%s)
  elapsed_time=$((current_time - START_TIME))
  if [ $elapsed_time -ge $TIMEOUT ]; then
    echo "$(date) [ERROR] Timeout reached. Pod did not become 'Running' within $TIMEOUT seconds."
    exit 1
  fi

  # Provide periodic updates with timestamps and elapsed time
  echo "$(date) [INFO] Waiting for 'csi-sanity' pod to be running... (Elapsed time: $elapsed_time seconds)"

  # Sleep for a short period before checking again
  sleep 1
done

oc exec -it csi-sanity -- sh -c "dnf install -qy fio strace nbd nmap-ncat qemu-img golang git"
oc exec -it csi-sanity -- sh -c "git clone https://github.com/kubernetes-csi/csi-test -b v5.3.1 --depth=1"
oc exec -it csi-sanity -- sh -c "cd csi-test && make"
oc exec -it csi-sanity -- sh -c "csi-test/cmd/csi-sanity/csi-sanity \
  --csi.controllerendpoint /var/lib/kubelet/plugins/kubesan-controller/socket \
  --csi.endpoint /var/lib/kubelet/plugins/kubesan-node/socket \
  --csi.mountdir /var/lib/kubelet/plugins/csi-sanity-target \
  --csi.stagingdir /var/lib/kubelet/plugins/csi-sanity-staging \
  --csi.testvolumeaccesstype block \
  --csi.testvolumeparameters /etc/csi-parameters/parameters \
  --csi.testvolumesize=1073741824 \
  --csi.testvolumeexpandsize=2147483648 \
  --ginkgo.succinct \
  --ginkgo.seed=1 \
  --ginkgo.junit-report=/tmp/csi-sanity.xml"

oc cp csi-sanity:/tmp/csi-sanity.xml ./csi-sanity.xml
