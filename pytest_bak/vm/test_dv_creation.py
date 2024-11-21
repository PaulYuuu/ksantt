import pytest
from kubernetes.dynamic import DynamicClient
from ocp_resources.datavolume import DataVolume
from ocp_resources.namespace import Namespace
from ocp_resources.storage_class import StorageClass
from timeout_sampler import TimeoutExpiredError

HTTP_URL = "https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-9-latest.x86_64.qcow2"
REGISTRY_URL = "docker://quay.io/containerdisks/centos-stream:9"


@pytest.mark.parametrize(
    "source, url",
    [("http", HTTP_URL), ("registry", REGISTRY_URL)],
    ids=["http", "registry"],
)
@pytest.mark.parametrize("access_modes", ["ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany"])
@pytest.mark.parametrize("volume_mode", ["Block", "Filesystem"])
class TestDvCreation:
    """Test class for testing DV creation with different volume/access modes and sources."""

    @pytest.fixture()
    def dv(
        self,
        dyn_client: DynamicClient,
        random_ns: Namespace,
        kubesan_sc: StorageClass,
        source: str,
        url: str,
        volume_mode: str,
        access_modes: str,
    ):
        """Fixture to init DV and return it."""
        sc_mode = kubesan_sc.instance.parameters.mode
        dv_name = f"dv-{sc_mode.lower()}-{source}-{volume_mode.lower()}-{access_modes.lower()}"

        dv = DataVolume(
            name=dv_name,
            namespace=random_ns.name,
            client=dyn_client,
            source=source,
            url=url,
            storage_class=kubesan_sc.name,
            access_modes=access_modes,
            volume_mode=volume_mode,
            size="10Gi",
            preallocation=True,
            teardown=False,
        )
        return dv

    def test_dv_create(self, dv: DataVolume):
        """Test creating a DV in the dynamically created test namespace"""
        try:
            # Create the DV in the test namespace
            dv.create()
            dv.logger.info(f"Created DV {dv.name} in namespace {dv.namespace}")

            # Wait for the DV to transition to 'Succeeded' status
            with pytest.raises(TimeoutExpiredError):
                dv.wait_for_dv_success(timeout=360)
            assert (
                dv.instance.status.progress == "100.0%"
            ), f"DV {dv.name} is not in 100% progress . Current status: {dv.instance.status}"

            dv.logger.info(
                f"DV {dv.name} is Created in namespace {dv.namespace} with "
                f"volume mode {dv.volume_mode} and access mode {dv.access_modes}"
            )
        except TimeoutExpiredError as e:
            pytest.fail(f"Failed to create DV: {str(e)}")

    @pytest.mark.skipif(
        not dv.exists,
        reason="Skipping test because the DV does not exist",
    )
    def test_dv_delete(self, dv: DataVolume):
        """Test deleting a DV."""
        # Delete the DV
        dv.delete(wait=True)
        dv.logger.info(f"Deleted DV {dv.name} from namespace {dv.namespace}")

        # Verify that the DV no longer exists
        assert not dv.exists, f"DV {dv.name} still exists after deletion"
        assert not dv.pvc.exists, f"The PVC({dv.pvc.name}) of {dv.name} still exists after deletion"
