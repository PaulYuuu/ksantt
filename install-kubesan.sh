VERSION=$(curl -s https://api.github.com/repos/kubernetes-csi/external-snapshotter/releases/latest | jq -r .tag_name)
oc create -k "https://github.com/kubernetes-csi/external-snapshotter/client/config/crd?ref=${VERSION}"
oc create -k "https://github.com/kubernetes-csi/external-snapshotter/deploy/kubernetes/snapshot-controller?ref=${VERSION}"
