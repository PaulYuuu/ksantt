import pytest
from kubernetes.client.exceptions import ApiException
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from ocp_resources.storage_class import StorageClass
from pytest_bdd import given, parsers, scenarios, then, when
from timeout_sampler import TimeoutExpiredError

scenarios("pvc_creation.feature")

@given(
    parsers.parse("define a PVC with accessModes {access_modes} and volumeMode {volume_mode}"),
    target_fixture="pvc"
)
def given_pvc(
    dynamic_client: DynamicClient,
    random_ns: Namespace,
    kubesan_sc: StorageClass,
    access_modes: str,
    volume_mode: str,
):
    """Fixture to init PVC and return it."""
    sc_mode = kubesan_sc.instance.parameters.mode
    pvc_name = f"pvc-{sc_mode.lower()}-{volume_mode.lower()}-{access_modes.lower()}"

    return PersistentVolumeClaim(
        name=pvc_name,
        namespace=random_ns.name,
        client=dynamic_client,
        storage_class=kubesan_sc.name,
        accessmodes=access_modes,
        volume_mode=volume_mode,
        size="1Gi",
        teardown=False,
    )

@when("I create a PVC")
def create_pvc(pvc: PersistentVolumeClaim):
    """Test creating a PVC in the dynamically created test namespace"""
    # Create the PVC in the test namespace
    with pytest.raises(ApiException) as api_info:
        pvc.create()
    if api_info.reason:
        if api_info.body:
            pvc.logger.error(f"HTTP response body: {api_info.body}")
        pytest.fail(f"API error occurred while creating PVC: {api_info.reason}")
    pvc.logger.info(f"Created PVC {pvc.name} in namespace {pvc.namespace}")

@then("the PVC should be Bound")
def pvc_should_be_bound(pvc):
    """Verify the PVC transitions to 'Bound' status."""
    with pytest.raises(TimeoutExpiredError) as exc_info:
        # Wait for the PVC to transition to 'Bound' status
        pvc.wait_for_status(PersistentVolumeClaim.Status.BOUND, timeout=60)
    if exc_info.value:
        pytest.fail(f"PVC did not reach 'Bound' status: {str(exc_info.value)}")
    pvc.logger.info(f"PVC {pvc.name} is Bound in namespace {pvc.namespace}")

@when("I delete the PVC")
def delete_pvc(pvc: PersistentVolumeClaim):
    """Delete the PVC only if it exists."""
    # Delete the PVC
    if not pvc.exists:
        pytest.skip(f"PVC {pvc.name} does not exist, skipping deletion.")
    pvc.delete(wait=True)
    pvc.logger.info(f"Deleted PVC {pvc.name} from namespace {pvc.namespace}.")

@then("the PVC should not exist")
def pvc_should_not_exist(pvc):
    """Verify the PVC no longer exists."""
    assert not pvc.exists, f"PVC {pvc.name} still exists after deletion."
