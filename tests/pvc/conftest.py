import pytest
from kubernetes import config
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.volume_snapshot_class import VolumeSnapshotClass
from ksantt.utils.persistent_volume_claim import pvc

import ksantt.utils
from ksantt.utils.options import KubeSanOptions


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