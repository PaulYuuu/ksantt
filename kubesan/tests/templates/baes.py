import random
import string
import logging
from kubernetes import client, config
import pytest
from openshift.dynamic import DynamicClient


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Reusable fixture for Kubernetes client
@pytest.fixture(scope="class")
def k8s_client():
    k8s_client = config.new_client_from_config()
    ocp_client = DynamicClient(k8s_client)
    return ocp_client.CoreV1Api()

# Reusable fixture for random namespace
@pytest.fixture
def random_namespace(k8s_client):
    namespace_name = "test-ns-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_name))
    k8s_client.create_namespace(namespace)
    logger.info(f"Namespace {namespace_name} created.")
    yield namespace_name
    k8s_client.delete_namespace(name=namespace_name, body=client.V1DeleteOptions())
    logger.info(f"Namespace {namespace_name} deleted.")

class TestPVC:
    def test_pvc_filesystem(self, k8s_client, random_namespace):
        """Test creating a PVC with Filesystem volume mode."""
        pvc_name = "pvc-filesystem"
        pvc_manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": pvc_name},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "1Gi"}},
                "storageClassName": "kube-san",
                "volumeMode": "Filesystem",
            },
        }
        response = k8s_client.create_namespaced_persistent_volume_claim(
            namespace=random_namespace, body=pvc_manifest
        )
        assert response.metadata.name == pvc_name
        pvc = k8s_client.read_namespaced_persistent_volume_claim(
            name=pvc_name, namespace=random_namespace
        )
        assert pvc.status.phase in ["Bound", "Pending"]
        logger.info(f"PVC {pvc_name} created in {random_namespace} with mode Filesystem.")

    def test_pvc_block(self, k8s_client, random_namespace):
        """Test creating a PVC with Block volume mode."""
        pvc_name = "pvc-block"
        pvc_manifest = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": pvc_name},
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": "1Gi"}},
                "storageClassName": "kube-san",
                "volumeMode": "Block",
            },
        }
        response = k8s_client.create_namespaced_persistent_volume_claim(
            namespace=random_namespace, body=pvc_manifest
        )
        assert response.metadata.name == pvc_name
        pvc = k8s_client.read_namespaced_persistent_volume_claim(
            name=pvc_name, namespace=random_namespace
        )
        assert pvc.status.phase in ["Bound", "Pending"]
        logger.info(f"PVC {pvc_name} created in {random_namespace} with mode Block.")
