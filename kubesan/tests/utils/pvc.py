from kubernetes import client
from kubernetes.client import CoreV1Api
from kubernetes.client.exceptions import ApiException

corev1 = CoreV1Api()

def create(name, storageClass, namespace="default", size="1Gi", accessModes="ReadWriteOnce", volumeMode="Block"):
    pvc_manifest = {
      "apiVersion": "v1",
      "kind": "PersistentVolumeClaim",
      "metadata": {
        "name": name
      },
      "spec": {
        "accessModes": [accessModes],
        "resources": {
            "requests": {
                "storage": size
            }
        },
        "storageClassName": storageClass,
        "volumeMode": volumeMode
      }
    }
    pvc = corev1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc_manifest)
    return pvc

def read(name, namespace="default"):
    return corev1.read_namespaced_persistent_volume_claim(name=name,namespace=namespace)

def delete(name, namespace="default"):
    corev1.delete_namespaced_persistent_volume_claim(
        name=name,
        namespace=namespace,
        body=client.V1DeleteOptions()
    )