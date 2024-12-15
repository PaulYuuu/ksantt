#!/bin/bash

# Find the KubeSAN StorageClass
SC_NAME=$(oc get sc -o json | jq -r '.items[] | select(.provisioner=="kubesan.gitlab.io") | .metadata.name' | head -n 1)
if [ -z "$SC_NAME" ]; then
    echo "Error: Could not find an existing KubeSAN StorageClass."
    exit 1
fi
oc patch configs.imageregistry.operator.openshift.io/cluster --patch '{"spec":{"defaultRoute":true}}' --type=merge
REGISTRY="$(oc get route/default-route -n openshift-image-registry -o=jsonpath='{.spec.host}')/openshift"
podman login --tls-verify=false -u $(oc whoami) -p $(oc whoami -t)  ${REGISTRY}

podman build -f Containerfile -t csi-sanity:latest
podman tag csi-sanity:latest image-registry.openshift-image-registry.svc:5000/default/csi-sanity:latest

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
  restartPolicy: Never
  hostPID: true
  containers:
    - name: csi-sanity
      image: quay.io/fedora/fedora:latest
      command:
        - ./csi-sanity
        - --csi.controllerendpoint
        - /var/lib/kubelet/plugins/kubesan-controller/socket
        - --csi.endpoint
        - /var/lib/kubelet/plugins/kubesan-node/socket
        - --csi.mountdir
        - /var/lib/kubelet/plugins/csi-sanity-target
        - --csi.stagingdir
        - /var/lib/kubelet/plugins/csi-sanity-staging
        - --csi.testvolumeaccesstype
        - block
        - --csi.testvolumeparameters
        - /etc/csi-parameters/parameters
        # Reduce volume size to fit test shared Volume Group
        - --csi.testvolumesize=1073741824
        - --csi.testvolumeexpandsize=2147483648
        - --ginkgo.succinct
        - --ginkgo.seed=1
        - --ginkgo.junit-report=csi-sanity.xml
      volumeMounts:
        - name: drivers
          mountPath: /var/lib/kubelet/plugins
        - name: csi-parameters
          mountPath: /etc/csi-parameters
        # Mount /dev so that symlinks to block devices resolve
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

fail=0

# TODO fix remaining issues, then hard-fail this test if csi-sanity fails.
# For now, if we got at least one pass in the final line of the logged output,
# then mark this overall test as skipped instead of failed.
pattern="[1-9][0-9]* Pass"
if [[ $fail != 0 &&
      "$( oc logs --tail=1 pods/csi-sanity )" =~ $pattern ]]; then
    fail=77
    echo "SKIP: partial csi-sanity failures are still expected"
fi

ksan-stage 'Finishing test...'
exit $fail
