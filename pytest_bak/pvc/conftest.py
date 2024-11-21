import pytest
from kubernetes.dynamic import DynamicClient
from ocp_resources.volume_snapshot_class import VolumeSnapshotClass

import ksantt.utils


@pytest.fixture(scope="module")
def kubesan_vsc(request: pytest.FixtureRequest, client: DynamicClient, sc_mode: str):
    """Fixture to create and return a KubeSAN StorageClass."""
    random_suffix = ksantt.utils.generate_random_string()
    vsc_name = f"kubesan-vsc-{random_suffix}"

    # Create the KubeSAN VolumeSnapshotClass
    with VolumeSnapshotClass(
        name=vsc_name,
        client=client,
        driver="kubesan.gitlab.io",
        delete_policy=VolumeSnapshotClass.ReclaimPolicy.DELETE,
    ) as vsc:
        vsc.logger.info(f"VolumeSnapshotClass '{vsc.name}' created")
        return vsc
