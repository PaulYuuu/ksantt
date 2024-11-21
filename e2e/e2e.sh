#!/bin/bash

set -ex

if [ -z "$KUBECONFIG" ]; then
    echo "KUBECONFIG is not set"
exit 1
fi

k8s_version=$(oc version | grep "Kubernetes Version" | awk '{print $3}' | awk -F '+' '{print $1}')

if [ ! -f e2e.test ]; then
    curl --location https://dl.k8s.io/${k8s_version}/kubernetes-test-linux-amd64.tar.gz | tar --strip-components=3 -zxf - kubernetes/test/bin/e2e.test kubernetes/test/bin/ginkgo
fi

KUBE_SSH_USER=core ./e2e.test \
    -ginkgo.focus='External.Storage.*kubesan.gitlab.io.*' \
    -ginkgo.skip='phemeral*' \
    -ginkgo.skip='SELinuxMountReadWriteOncePod.*' \
    -ginkgo.skip='subpath.*' \
    -ginkgo.skip='different volume mode.*' \
    -ginkgo.skip='after modifying source data.*' \
    -ginkgo.skip='\((?:xfs|filesystem volmode|ntfs|ext4)\).*' \
    -ginkgo.skip='default fs.*' \
    -ginkgo.skip='volumeMount.*' \
    -ginkgo.skip='files.*' \
    -storage.testdriver=./kubesan-driver.yaml \
    -provider=local \
    -allowed-not-ready-nodes -1
