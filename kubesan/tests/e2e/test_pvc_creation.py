import pytest
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
import time
from openshift.dynamic import DynamicClient
import random
import string

from ..utils import pvc as pvc_utils

# Load Kubernetes configuration (use KUBECONFIG or default kubeconfig)
@pytest.fixture
def k8s_client():
    k8s_client = config.load_kube_config()
    ocp_client = DynamicClient(k8s_client)
    ocp_client.resources
    v1 = ocp_client.resources.get(api_version='v1', kind='PersistentVolumeClaim')

# Test PVC creation and verify it becomes Bound with Block VolumeMode
@pytest.mark.parametrize("volume_mode", ["Block", "Filesystem"])
@pytest.mark.parametrize("access_modes", ["ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany"])
def test_create_pvc(volume_mode, access_modes, k8s_client):
    if volume_mode == "Filesystem" and access_modes == "ReadWriteMany":
        pytest.skip("Skipping Filesystem + ReadWriteMany combination as not supported")
    namespace = "pvc-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    pvc_name = f"pvc-{volume_mode.lower()}-{access_modes.lower()}"

    # Create the PVC
    try:
        response = pvc_utils.create(pvc_name, namespace=namespace, accessModes=access_modes, volumeMode=volume_mode)
        assert response.metadata.name == pvc_name
    except ApiException as e:
        pytest.fail(f"PVC creation failed: {e}")

    # Verify PVC reaches the Bound phase
    pvc_bound = False
    timeout = 60  # Timeout in seconds
    interval = 5  # Polling interval in seconds
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            pvc = pvc_utils.read(pvc_name)
            if pvc.status.phase == "Bound":
                pvc_bound = True
                break
        except ApiException as e:
            pytest.fail(f"Failed to read PVC: {e}")
        time.sleep(interval)

    if not pvc_bound:
        try:
            pvc = k8s_client.read_namespaced_persistent_volume_claim(
                name=pvc_name,
                namespace=namespace
            )
            if pvc.status.conditions:
                for condition in pvc.status.conditions:
                    print(f"Condition: {condition.type}, Status: {condition.status}, Reason: {condition.reason}, Message: {condition.message}")
            else:
                print("No conditions available.")
        except ApiException as e:
            print(f"Failed to describe PVC: {e}")

    assert pvc_bound, "PVC did not reach the Bound state within the timeout period."

# Cleanup after the test
@pytest.fixture(scope="module", autouse=True)
def cleanup_pvc(k8s_client):
    yield  # Wait for the test to finish
    namespace = "default"
    try:
        k8s_client.delete_namespaced_persistent_volume_claim(
            name="test-pvc-kubesan-block",
            namespace=namespace,
            body=client.V1DeleteOptions()
        )
    except ApiException as e:
        print(f"Cleanup failed: {e}")
