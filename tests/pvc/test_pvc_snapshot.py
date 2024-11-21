import pytest
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from ocp_resources.storage_class import StorageClass
from timeout_sampler import TimeoutExpiredError


class TestPvcSnapshot:
    """Test class for testing PVC volumesnapshot."""
    def test_pvc_create(self, pvc: PersistentVolumeClaim):
        """Test creating a PVC in the dynamically created test namespace"""
        try:
            # Create the PVC in the test namespace
            pvc.create()
            pvc.logger.info(f"Created PVC {pvc.name} in namespace {pvc.namespace}")

            # Wait for the PVC to transition to 'Bound' status
            pvc.wait_for_status(PersistentVolumeClaim.Status.BOUND, timeout=60)
            assert pvc.bound(), f"PVC {pvc.name} is not Bound. Current status: {pvc.status}"

            pvc.logger.info(
                f"PVC {pvc.name} is Bound in namespace {pvc.namespace} with "
                f"volume mode {pvc.volume_mode} and access mode {pvc.accessmodes}"
            )
        except TimeoutExpiredError as e:
            pytest.fail(f"Failed to create PVC: {str(e)}")

    @pytest.mark.skipif(
        not pvc.exists,
        reason="Skipping test because the PVC does not exist",
    )
    def test_pvc_delete(self, pvc: PersistentVolumeClaim):
        """Test deleting a PVC."""
        # Delete the PVC
        pvc.delete(wait=True)
        pvc.logger.info(f"Deleted PVC {pvc.name} from namespace {pvc.namespace}.")

        # Verify that the PVC no longer exists
        assert not pvc.exists, f"PVC {pvc.name} still exists after deletion."
