from behave import given, then, when
from behave.runner import Context
from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from timeout_sampler import TimeoutExpiredError

from utils import rp_attach_json


@given("a PVC specification with access mode {access_modes} and storage mode {volume_mode}")
def define_pvc(context: Context, access_modes: str, volume_mode: str):
    """
    Define a new PersistentVolumeClaim object with the given configuration parameters.

    Args:
        context: Behave context containing test configuration and resources
        access_modes: Storage access mode (e.g., ReadWriteOnce, ReadOnlyMany)
        volume_mode: Volume mode for the storage (e.g., Block, Filesystem)
    """
    sc_mode = context.sc.instance.parameters.mode
    pvc_name = f"pvc-{sc_mode.lower()}-{volume_mode.lower()}-{access_modes.lower()}"

    pvc = PersistentVolumeClaim(
        name=pvc_name,
        namespace=context.ns.name,
        client=context.client,
        storage_class=context.sc.name,
        accessmodes=access_modes,
        volume_mode=volume_mode,
        size="1Gi",
    )
    if context.rph:
        pvc.logger.addHandler(context.rph)
    pvc.to_dict()
    context.pvc = pvc
    rp_attach_json(context.log.info, "Defined PersistentVolumeClaim with manifest", "pvc.json", pvc.res)


@when("I create the PVC")
def create_pvc(context: Context):
    """
    Create a new PersistentVolumeClaim instance in the cluster using the predefined specification.

    Args:
        context: Behave context containing the PVC object to be created
    """
    context.pvc.create()


@then("the PVC status should change to Bound")
def pvc_should_be_bound(context: Context):
    """
    Monitor the PVC status and wait for it to reach the Bound state.

    Args:
        context: Behave context containing the PVC to verify

    Raises:
        TimeoutExpiredError: If the PVC fails to reach 'Bound' status within timeout
    """
    try:
        context.pvc.wait_for_status(PersistentVolumeClaim.Status.BOUND, timeout=60)
        context.log.info(f"PersistentVolumeClaim {context.pvc.name} is bound")
    except TimeoutExpiredError:
        rp_attach_json(
            context.log.debug,
            f"PersistentVolumeClaim is in {context.pvc.status} status",
            "pvc_instance.json",
            context.pvc.instance.to_dict(),
        )
        raise


@when("I perform a deletion of the PVC")
def delete_pvc(context: Context):
    """
    Remove the PersistentVolumeClaim from the cluster and ensure deletion is finished.

    Args:
        context: Behave context containing the PVC to delete
    """
    context.pvc.delete(wait=True)
    context.log.info(f"PersistentVolumeClaim {context.pvc.name} is deleted")


@then("the PVC should be completely removed")
def pvc_should_not_exist(context: Context):
    """
    Verify that the PersistentVolumeClaim has been completely removed from the system.

    Args:
        context: Behave context containing the PVC to verify

    Raises:
        AssertionError: If the PVC still exists after deletion
    """
    assert not context.pvc.exists, f"PersistentVolumeClaim '{context.pvc.name}' still exists after deletion."
    context.log.info(f"PersistentVolumeClaim '{context.pvc.name}' no longer exists")
