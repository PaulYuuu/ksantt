import pytest
from kubernetes.client.exceptions import ApiException
from kubernetes.dynamic import DynamicClient
from ocp_resources.namespace import Namespace
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from ocp_resources.volumesnapshot import VolumeSnapshot
from ocp_resources.volumesnapshotclass import VolumeSnapshotClass
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("features/pvc_snapshot.feature")


# Fixture to create a PVC
@pytest.fixture
def pvc(random_ns: Namespace, dynamic_client: DynamicClient):
    pvc = PersistentVolumeClaim(
        name="test-pvc",
        namespace=random_ns.name,
        client=dynamic_client,
        storage_class="standard",  # Use a predefined storage class
        accessmodes="ReadWriteOnce",
        volume_mode="Block",
        size="1Gi",
        teardown=False,
    )
    yield pvc


# Fixture to create a VolumeSnapshotClass with a specific label
@pytest.fixture
def volumesnapshotclass(dynamic_client: DynamicClient, request):
    label = request.param.get("label")
    snapshot_class = VolumeSnapshotClass(
        name=f"snapshot-class-{label}",
        client=dynamic_client,
        driver="external-snapshotter",
        deletion_policy=VolumeSnapshotClass.DeletionPolicy.RETAIN,
        labels={"type": label},
    )
    yield snapshot_class


# Step to define a PVC
@given(parsers.parse("define a PVC with access mode {access_modes} and volume mode {volume_mode}"))
def define_pvc(access_modes, volume_mode, pvc):
    pvc.accessmodes = access_modes
    pvc.volume_mode = volume_mode
    pvc.create()


# Step to create a VolumeSnapshotClass with a label
@given("create a VolumeSnapshotClass with the label {label}")
def create_volumesnapshotclass(volumesnapshotclass, label):
    volumesnapshotclass.create()
    volumesnapshotclass.logger.info(f"Created VolumeSnapshotClass with label '{label}'")


# Step to create a VolumeSnapshot from the PVC
@when("I create a VolumeSnapshot for the PVC")
def create_volumesnapshot(
    dynamic_client: DynamicClient,
    pvc: PersistentVolumeClaim,
    volumesnapshotclass: VolumeSnapshotClass,
):
    volume_snapshot_name = f"snapshot-{pvc.name}"
    snapshot = VolumeSnapshot(
        name=volume_snapshot_name,
        namespace=pvc.namespace,
        client=dynamic_client,
        volume_snapshot_class=volumesnapshotclass.name,
        source=pvc,
    )
    snapshot.create()


# Step to verify the VolumeSnapshot is created and bound
@then("the VolumeSnapshot should be created and Bound")
def volumesnapshot_should_be_bound(dynamic_client: DynamicClient, pvc: PersistentVolumeClaim):
    volume_snapshot = VolumeSnapshot.get(pvc.namespace, f"snapshot-{pvc.name}", dynamic_client)
    assert volume_snapshot.status == "Bound", "VolumeSnapshot is not in Bound state"


# Step to delete the VolumeSnapshot
@then("I delete the VolumeSnapshot")
def delete_volumesnapshot(dynamic_client: DynamicClient, pvc: PersistentVolumeClaim):
    volume_snapshot = VolumeSnapshot.get(pvc.namespace, f"snapshot-{pvc.name}", dynamic_client)
    volume_snapshot.delete()
    volume_snapshot.logger.info(f"Deleted VolumeSnapshot for PVC {pvc.name}")


# Step to ensure the VolumeSnapshot no longer exists
@then("the VolumeSnapshot should not exist")
def volumesnapshot_should_not_exist(dynamic_client: DynamicClient, pvc: PersistentVolumeClaim):
    with pytest.raises(ApiException):
        VolumeSnapshot.get(pvc.namespace, f"snapshot-{pvc.name}", dynamic_client)
