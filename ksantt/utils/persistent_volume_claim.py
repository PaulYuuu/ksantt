from kubernetes import client
from kubernetes.client import CoreV1Api
from kubernetes.dynamic import DynamicClient
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim

corev1 = CoreV1Api()


def create(name, storageClass, namespace="default", size="1Gi", accessModes="ReadWriteOnce", volumeMode="Block"):
    pvc_manifest = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": name},
        "spec": {
            "accessModes": [accessModes],
            "resources": {"requests": {"storage": size}},
            "storageClassName": storageClass,
            "volumeMode": volumeMode,
        },
    }
    pvc = corev1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc_manifest)
    return pvc


def read(name, namespace="default"):
    return corev1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)


def delete(name, namespace="default"):
    corev1.delete_namespaced_persistent_volume_claim(name=name, namespace=namespace, body=client.V1DeleteOptions())


def pvc(
    name: str,
    namespace: str,
    storage_class: str,
    volume_mode: str,
    access_modes: str,
    size: str,
    client: DynamicClient | None = None,
    teardown: bool = True,
):
    pvc = PersistentVolumeClaim(
        name=name,
        namespace=namespace,
        client=client,
        storage_class=storage_class,
        accessmodes=access_modes,
        volume_mode=volume_mode,
        size=size,
        teardown=teardown,
    )
    return pvc
